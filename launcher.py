from time import sleep
from Process import Process


def launch(nb_process, running_time=5):
    processes = []

    for i in range(nb_process):
        processes = processes + [Process("P"+str(i), nb_process)]

    sleep(running_time)

    for p in processes:
        p.stop()

    for p in processes:
        p.wait_stopped()


if __name__ == '__main__':

    # bus = EventBus.getInstance()

    launch(nb_process=3, running_time=10)

    # bus.stop()
