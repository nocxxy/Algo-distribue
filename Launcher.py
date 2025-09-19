from time import sleep
from Process import Process

def launch(nbProcess, runningTime=5):
    processes = []

    # Attribution directe d'IDs uniques au démarrage
    for i in range(nbProcess):
        p = Process("P"+str(i))
        processes.append(p)

    # Attendre que les processus s'initialisent et élisent un leader
    sleep(runningTime)

    for p in processes:
        p.stop()

    for p in processes:
        p.waitStopped()

if __name__ == '__main__':
    # Augmenter le temps pour permettre plus de chances d'élection
    launch(nbProcess=3, runningTime=5)  # Temps augmenté pour laisser plus de chances à l'élection