from threading import Lock, Thread

import threading

from time import sleep

from pyeventbus3.pyeventbus3 import *

from BroadcastSyncMessage import *

from OneToOneSyncMessage import *

from BroadcastMessage import *

from NumberingMessage import *

from OneToOneMessage import *

from Synchronize import *

from Lamport import *

from Token import *

import random as rd

class Com:
    def __init__(self, my_id, nb_process: int) -> None:
        self.my_id = my_id
        self.nb_process = nb_process

        self.lamport = Lamport()

        PyBus.Instance().register(self, self)

        self.token_status = TokenStatus.NONE

        self.mailbox = []

        self.synchronize_message = None
        
        self.token_request = Lock()
        self.token_sc = Lock()

        self.nb_process_synchronized = 0

        self.broadcast_sync_nb_received_message = 0

        self.awating_acknowledgment = False

        self.alive = True

        self.numbering_m_value = nb_process * 1_000_000

        self.numbering_list = []

        self.timeout = 5

        if self.my_id == self.nb_process - 1:
            self.init_token()


    def inc_clock(self) -> None:
        """
        Incrémente l'horloge de Lamport.
        """

        self.lamport.increment_clock()


    def get_next_process_id(self) -> None:
        """
        Retourne l'ID du processus suivant
        """

        return (self.my_id + 1) % self.nb_process


    def init_token(self) -> None:
        """
        Envoie le Token pour la première fois.
        Celui-ci se déplacera avec une topologie en anneau.
        """

        PyBus.Instance().post(Token(receiver = 0))

    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def on_token(self, token: Token) -> None:
        """
        Gère le Token, celui-ci est immédatiement renvoyé, sauf si un accès à la section critique est demandé.
        """

        if not self.alive:
            return

        if token.receiver != self.my_id:
            return

        if self.token_status == TokenStatus.REQUESTED:
            print(f"Token acquired by P{self.my_id}")

            self.token_status = TokenStatus.POSSESSED

            self.token_request.release()
            self.token_sc.acquire()

            self.token_status = TokenStatus.NONE

            PyBus.Instance().post(Token(receiver = self.get_next_process_id()))

        else:
            PyBus.Instance().post(Token(receiver = self.get_next_process_id()))



    def request_sc(self):
        """
        Place le processus en attente d'un accès à la zone critique (le token).
        """

        print(f"Token requested by P{self.my_id}")

        self.token_status = TokenStatus.REQUESTED

        self.token_request.acquire()


    def release_sc(self):
        """
        Sort de la zone critique (libère le token).
        """

        print(f"Token released by P{self.my_id}")

        self.token_status = TokenStatus.RELEASED

        self.token_sc.release()


    def broadcast(self, message):
        """
        Envoie un message à tous les autres processus.
        """

        self.lamport.increment_clock()

        broadcast_message = BroadcastMessage(timestamp=self.lamport.clock,
                                          content=message, sender_id=self.my_id)

        print("=========")
        print(f"{self.my_id} sends \"{broadcast_message.content}\"")
        
        PyBus.Instance().post(broadcast_message)


    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def on_broadcast(self, message: BroadcastMessage):
        """
        Traite les messages envoyés en broadcast.
        """

        if message.sender_id == self.my_id:
            return

        self.lamport.set_lamport_clock(timestamp = message.timestamp)

        self.mailbox.append(message)

        print("=========")
        print(f"{self.my_id} received \"{message.content}\" from {message.sender_id}, process' Lamport clock is at {self.lamport.clock}")


    def send_to(self, message, to: int):
        """
        Envoie un message à un processus en particulier.
        """

        self.lamport.increment_clock()

        one_to_one_message = OneToOneMessage(timestamp=self.lamport.clock,
                                          content=message, sender_id=self.my_id, recipient_id=to)

        PyBus.Instance().post(one_to_one_message)


    @subscribe(threadMode=Mode.PARALLEL, onEvent=OneToOneMessage)
    def on_receive(self, message):
        """
        Traite les messages destinés à un processus dédié.
        """

        if message.sender_id == self.my_id or message.recipient_id != self.my_id:
            return

        self.lamport.set_lamport_clock(timestamp = message.timestamp)

        self.mailbox.append(message)

        print("=========")
        print(f"{self.my_id} received one to one message \"{message.content}\" from {message.sender_id}, process' Lamport clock is at {self.lamport.clock}")


    def stop(self):
        """
        Tue le communicateur.
        """
        self.alive = False


    @subscribe(threadMode=Mode.PARALLEL, onEvent=Synchronize)
    def on_synchronize(self, _message):
        """
        Traite les messages de synchronisation.
        """
        self.nb_process_synchronized += 1


    def synchronize(self) -> None:
        """
        Synchronise l'ensemble des processus.
        Utilise une topologie distribuée.
        """

        PyBus.Instance().post(Synchronize())

        while self.nb_process_synchronized < self.nb_process:
            pass

        self.nb_process_synchronized = 0

        print(f"P{self.my_id} synchronized.")


    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastSyncMessage)
    def on_broadcast_sync(self, message) -> None:
        """
        Traite les messages de broadcast synchronisés, avec acquitement.
        """

        if message.sender_id == self.my_id:
            return

        if message.recipient_id is None:
            self.lamport.set_lamport_clock(timestamp = message.timestamp)

            self.mailbox.append(message)

            PyBus.Instance().post(BroadcastSyncMessage(timestamp = self.lamport.clock, content = message.content, sender_id = self.my_id, recipient_id = message.sender_id))

        elif message.recipient_id == self.my_id:
            self.broadcast_sync_nb_received_message += 1


    def broadcast_sync(self, message) -> None:
        """
        Envoie un message à tous les autres processus de manière synchrone, avec demande d'acquitement.
        """

        self.lamport.increment_clock()

        broadcast_sync_message = BroadcastSyncMessage(timestamp=self.lamport.clock,
                                          content=message, sender_id=self.my_id)

        print("=========")
        print(f"{self.my_id} sends in sync \"{broadcast_sync_message.content}\"")
        
        PyBus.Instance().post(broadcast_sync_message)

        while self.broadcast_sync_nb_received_message < self.nb_process - 1:
            pass

        print("Message broadcasted in sync.")

        self.broadcast_sync_nb_received_message = 0


    @subscribe(threadMode=Mode.PARALLEL, onEvent=OneToOneSyncMessage)
    def on_receive_sync(self, message) -> None:
        """
        Traite les messages destinés à un processus dédié de manière synchrone, avec acquitement.
        """

        if message.sender_id == self.my_id or message.recipient_id != self.my_id:
            return

        if self.awating_acknowledgment:
            self.awating_acknowledgment = False

        else:
            self.lamport.set_lamport_clock(timestamp = message.timestamp)

            self.mailbox.append(message)

            print("=========")
            print(f"{self.my_id} received one to one message in sync \"{message.content}\" from {message.sender_id}, process' Lamport clock is at {self.lamport.clock}")

            PyBus.Instance().post(OneToOneSyncMessage(timestamp = self.lamport.clock, content = message.content, sender_id = self.my_id, recipient_id = message.sender_id))


    
    def send_to_sync(self, message, to: int) -> None:
        """
        Traite les messages destinés à un processus dédié.
        """

        self.lamport.increment_clock()

        one_to_one_sync_message = OneToOneSyncMessage(timestamp=self.lamport.clock,
                                          content=message, sender_id=self.my_id, recipient_id=to)

        self.awating_acknowledgment = True

        PyBus.Instance().post(one_to_one_sync_message)

        while self.awating_acknowledgment:
            pass

        print("Received acknowledgment.")
