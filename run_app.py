"""Entry point for the packaged app. `--selftest` checks USB access without opening a window; `--diagnose` saves a troubleshooting report."""
import sys

if __name__ == "__main__":
    if "--diagnose" in sys.argv:
        from hobo.diagnose import write_report
        print("Wrote", write_report())
    elif "--selftest" in sys.argv:
        from hobo.actions import describe
        from hobo.device import Logger, logger_present
        print("logger present:", logger_present())
        if logger_present():
            with Logger() as lg:
                print(describe(lg))
    else:
        from hobo.gui import run
        run()
