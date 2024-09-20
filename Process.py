from threading import Lock, Thread

from time import sleep

# from geeteventbus.subscriber import subscriber
# from geeteventbus.eventbus import eventbus
# from geeteventbus.event import event

from pyeventbus3.pyeventbus3 import *

#####################################

from Com import *

from Token import *

from Message import *

from BroadcastMessage import *

from OneToOneMessage import *


class Process(Thread):

    # nb_process_created = 0

    def __init__(self, name, nb_process):
        Thread.__init__(self)

        self.nb_process = nb_process

        self.com = Com(nb_process = self.nb_process)

        self.my_process_name = name
        self.setName("MainThread-" + name)

        self.alive = True

        self.start()
        
    def run(self):

        self.com.numbering()

        loop = 0
        while self.alive:
            print(self.getName() + " Loop: " + str(loop))
            sleep(1)


            # Broadcast et sendTo
            # if self.my_process_name == "P1":
            #     # b1 = Bidule("ga")
            #     # b2 = Bidule("bu")
            #     # print(self.getName() + " send: " + b1.getMachin())
            #     # PyBus.Instance().post(b1)

            #     self.com.broadcast("Coucou")
            #     self.com.send_to("Direct message", 2)

            
            # Section critique
            # if self.my_process_name == "P2":
            #     self.com.request_sc()

            #     sleep(3)

            #     self.com.release_sc()
            
            
            # Synchronisation
            # if loop == 4:
            #     self.com.synchronize()


            # Broadcast sync
            # if self.my_process_name == "P2":
            #     self.com.broadcast_sync("Test broadcast in sync!")


            # Send to sync
            if self.my_process_name == "P2":
                self.com.send_to_sync("Test one to one in sync!", 0)

            loop += 1

        self.com.stop()

        print(self.getName() + " stopped")

    def stop(self):
        self.alive = False
        

    def wait_stopped(self):
        self.join()
