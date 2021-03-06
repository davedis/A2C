import tensorflow as tf
import numpy as np
import gym


class A2C:
    def __init__(self):
        self.game = gym.make('CartPole-v1')
        self.num_actions = self.game.action_space.n
        self.state_size = self.game.observation_space.shape[0]

        self.state_input = tf.placeholder(tf.float32, [None, self.state_size])

        # Define any additional placeholders needed for training your agent here:

        self.rewards = tf.placeholder(shape=[None], dtype=tf.float32)
        self.actions = tf.placeholder(shape=[None], dtype =tf.int32)

        self.state_value = self.critic()
        self.actor_probs = self.actor()
        self.loss_val = self.loss()
        self.train_op = self.optimizer()
        self.session = tf.Session()
        self.session.run(tf.global_variables_initializer())

    def optimizer(self):
        """
        :return: Optimizer for your loss function
        """
        return tf.train.AdamOptimizer(.001).minimize(self.loss_val)

    def critic(self):
        """
        Calculates the estimated value for every state in self.state_input. The critic should not depend on
        any other tensors besides self.state_input.
        :return: A tensor of shape [num_states] representing the estimated value of each state in the trajectory.
        """
        hidden_sz = 30

        U = tf.Variable(tf.random_normal([self.state_size, hidden_sz],dtype=tf.float32,stddev=.1))
        bU = tf.Variable(tf.random_normal([hidden_sz]))

        L1_output = tf.nn.relu(tf.matmul(self.state_input,U)+bU)
        
        V = tf.Variable(tf.random_normal([hidden_sz,1],dtype=tf.float32,stddev=.1))

        L2_output = tf.matmul(L1_output,V)

        return tf.squeeze(L2_output)
        

    def actor(self):
        """
        Calculates the action probabilities for every state in self.state_input. The actor should not depend on
        any other tensors besides self.state_input.
        :return: A tensor of shape [num_states, num_actions] representing the probability distribution
            over actions that is generated by your actor.
        """
        hidden_sz = 30
       
        W = tf.Variable(tf.random_uniform([self.state_size,hidden_sz], dtype=tf.float32))
        bW = tf.Variable(tf.random_uniform([hidden_sz],dtype = tf.float32))

        L1_output = tf.nn.relu(tf.matmul(self.state_input,W)+bW)
        
        T = tf.Variable(tf.random_uniform([hidden_sz,self.num_actions]))
        bT = tf.Variable(tf.random_uniform([self.num_actions]))

        L2_output = tf.matmul(L1_output,T)+bT
        actor_probs = tf.nn.softmax(L2_output)
        print("actor output shape: ", tf.shape(actor_probs))
        return actor_probs

    def loss(self):
        """
        :return: A scalar tensor representing the combined actor and critic loss.
        """
        indices = tf.range(0, tf.shape(self.actor_probs)[0])*2 + self.actions
        actor_out = tf.gather(tf.reshape(self.actor_probs, [-1]), indices)
        advantage = self.rewards-self.state_value
        actor_loss = -tf.reduce_sum(tf.log(actor_out)*advantage)
        critic_loss = tf.reduce_sum(tf.square(self.rewards - self.state_value))
        loss = actor_loss + critic_loss
        return loss

    def train_episode(self):
        """
        train_episode will be called 1000 times by the autograder to train your agent. In this method,
        run your agent for a single episode, then use that data to train your agent. Feel free to
        add any return values to this method.
        """
        rewards = []
        actions = []
        states = []
        env = self.game
        done = False
        state = env.reset()

        while not done:
            act_dist = self.session.run(self.actor_probs, feed_dict = {
                                                                        self.state_input: state[np.newaxis],
                                                                        })
            action = np.random.choice(self.num_actions, p = np.squeeze(act_dist))
            next_state, reward, done, _ = env.step(action)
            states.append(state)
            rewards.append(reward)
            actions.append(action)
            state = next_state

        if done:
            discounted_rewards = [0]*(len(rewards))
            gamma = .99
            n = len(rewards)
            discounted_rewards[n-1] = rewards[n-1]
            for i in range(len(rewards)-2, 0, -1):
                discounted_rewards[i] = rewards[i]+gamma*discounted_rewards[i+1]

            self.session.run(self.train_op, feed_dict = {
                                                        self.state_input : states,
                                                        self.actions : actions,
                                                        self.rewards : discounted_rewards
                                                        })
        return np.sum(rewards)



def check_actor(model):
    """
    The autograder will use your actor() function to test your agent. This function
    checks that your actor returns a tensor of the right shape for the autograder.
    :return: True if the model's actor returns a tensor of the correct shape.
    """
    dummy_state = np.ones((10, 4))
    actor_probs = model.session.run(model.actor_probs, feed_dict={
        model.state_input: dummy_state
    })
    return actor_probs.shape == (10, 2)


if __name__ == '__main__':
    # Change __main__ to train your agent for 1000 episodes and print the average reward over the last 100 episodes.
    # The code below is similar to what our autograder will be running.

    learner = A2C()
    tot_Rs = []
    for i in range(1000):
        total_reward =learner.train_episode()
        tot_Rs.append(total_reward)
        print(total_reward)
    print(np.mean(tot_Rs[-100:]))
    assert(check_actor(learner))

