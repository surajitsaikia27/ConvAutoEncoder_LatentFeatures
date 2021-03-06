import tensorflow as tf
import numpy as np
from matplotlib import pyplot as plt
import glob
import cv2
from test_generate_labels import train_images
from models import *
from mnist import MNIST  # this is the MNIST data manager that provides training/testing batches


class ConvolutionalAutoencoder(object):
    """

    """
    def __init__(self):
        """
        build the graph
        """
        # place holder of input data
        x = tf.placeholder(tf.float32, shape=[None, 64, 64, 3])  # [#batch, img_height, img_width, #channels]

        # encode
        conv1 = Convolution2D([5, 5, 3, 32], activation=tf.nn.relu, scope='conv_1')(x)
        pool1 = MaxPooling(kernel_shape=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME', scope='pool_1')(conv1)
        conv2 = Convolution2D([5, 5, 32, 32], activation=tf.nn.relu, scope='conv_2')(pool1)
        pool2 = MaxPooling(kernel_shape=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME', scope='pool_2')(conv2)
        unfold = Unfold(scope='unfold')(pool2)
        encoded = FullyConnected(80, activation=tf.nn.relu, scope='encode')(unfold)
        # decode
        decoded = FullyConnected(16*16*32, activation=tf.nn.relu, scope='decode')(encoded)
        fold = Fold([-1, 16, 16, 32], scope='fold')(decoded)
        unpool1 = UnPooling((2, 2), output_shape=tf.shape(conv2), scope='unpool_1')(fold)
        deconv1 = DeConvolution2D([5, 5, 32, 32], output_shape=tf.shape(pool1), activation=tf.nn.relu, scope='deconv_1')(unpool1)
        unpool2 = UnPooling((2, 2), output_shape=tf.shape(conv1), scope='unpool_2')(deconv1)
        reconstruction = DeConvolution2D([5, 5, 3, 32], output_shape=tf.shape(x), activation=tf.nn.sigmoid, scope='deconv_2')(unpool2)

        # loss function
        loss = tf.nn.l2_loss(x - reconstruction)  # L2 loss

        # training
        training = tf.train.AdamOptimizer(1e-4).minimize(loss)

        #
        self.x = x
        self.reconstruction = reconstruction
        self.loss = loss
        self.training = training
        self.encoded = encoded
    def train(self, batch_size, passes, new_training=True):
        """

        :param batch_size:
        :param passes:
        :param new_training:
        :return:
        """
        mnist = MNIST()

        with tf.Session() as sess:
            # prepare session
            if new_training:
                saver, global_step = Model.start_new_session(sess)
            else:
                saver, global_step = Model.continue_previous_session(sess, ckpt_file='saver/checkpoint')

            # start training
            for step in range(1+global_step, 1+passes+global_step):
                #x, y = mnist.get_batch(batch_size)
                x,_ = train_images()
                self.training.run(feed_dict={self.x: x})

                if step % 10 == 0:
                    loss = self.loss.eval(feed_dict={self.x: x})
                    print("pass {}, training loss {}".format(step, loss))

                if step % 10 == 0:  # save weights
                    saver.save(sess, 'saver/cnn', global_step=step)
                    print('checkpoint saved')

    def reconstruct(self):
        """

        """
        def weights_to_grid(weights, rows, cols):
            """convert the weights tensor into a grid for visualization"""
            height, width, in_channel, out_channel = weights.shape
            print(height,width,in_channel,out_channel, rows * cols - out_channel)
            padded = np.pad(weights, [(1, 1), (1, 1), (0, 0), (0, rows * cols - out_channel)],
                            mode='constant', constant_values=0)
            transposed = padded.transpose((3, 1, 0, 2))
            reshaped = transposed.reshape((rows, -1))
            grid_rows = [row.reshape((-1, height + 2, in_channel)).transpose((1, 0, 2)) for row in reshaped]
            grid = np.concatenate(grid_rows, axis=0)

            return grid.squeeze()

        mnist = MNIST()

        with tf.Session() as sess:
            saver, global_step = Model.continue_previous_session(sess, ckpt_file='saver/checkpoint')

            # visualize weights
            first_layer_weights = tf.get_default_graph().get_tensor_by_name("conv_1/kernel:0").eval()
            grid_image = weights_to_grid(first_layer_weights, 4, 8)

            fig, ax0 = plt.subplots(ncols=1, figsize=(8, 4))
            ax0.imshow(grid_image, cmap=plt.cm.gray, interpolation='nearest')
            ax0.set_title('first conv layers weights')
            plt.show()

            # visualize results
            batch_size = 36
            #x, y = mnist.get_batch(batch_size, dataset='testing')
            x,_ = train_images()
            org, recon = sess.run((self.x, self.reconstruction), feed_dict={self.x: x})
            for image in glob.glob("/home/surajit/Desktop/datasets/outex/*.bmp"):
                img=cv2.imread(image)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img=cv2.resize(img,(64,64))
                img=img.reshape(1,64,64,3)
                activation = sess.run(self.encoded, feed_dict={self.x: img})
                print('Activation',activation[0])




def main():
    conv_autoencoder = ConvolutionalAutoencoder()
    # conv_autoencoder.train(batch_size=100, passes=100000, new_training=True)
    #conv_autoencoder.train(64,10000)
    conv_autoencoder.reconstruct()


if __name__ == '__main__':
    main()
