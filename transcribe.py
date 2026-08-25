import multiprocessing
import tkinter as tk

from app import TranscribeApp


def main():
    root = tk.Tk()
    TranscribeApp(root)
    root.mainloop()


if __name__ == "__main__":
    # Windows / PyInstallerでmultiprocessingを使うために必要
    multiprocessing.freeze_support()

    main()