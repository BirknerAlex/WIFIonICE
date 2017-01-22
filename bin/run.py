import sys
import logging
import time
import getpass
import psutil
import random
import sh
import uuid
import platform

class WIFIonICE:

    TRAFFIC_LIMIT = 180

    def __init__(self):
        self.logger = logging.getLogger("WIFIonICE")
        self.init_usage = self.traffic_usage()

        if self.init_usage >= self.TRAFFIC_LIMIT:
            self.logger.info("Initial reconnect because the script don't know if the limit has been already exeeded.")
            self.reconnect()

        self.run()

    """
    Returns the current traffic usage from the network interfaces

    """
    def traffic_usage(self):
        psutil.net_io_counters()

        sent = int(psutil.net_io_counters().bytes_sent) / 1000000
        received = int(psutil.net_io_counters().bytes_recv) / 1000000

        return round(sent + received)

    def reconnect(self):
        network_setup = sh.Command("/usr/sbin/networksetup")
        network_setup("-removepreferredwirelessnetwork", "en0", "WIFIonICE")

        scutil = sh.Command("/usr/sbin/scutil")
        scutil("–-set", "HostName", self.generate_new_hostname())

        ifconfig = sh.Command("/sbin/ifconfig")
        ifconfig("en0", "ether", self.generate_new_mac())

        network_setup("-setairportnetwork", "en0", "WIFIonICE")
        self.init_usage = self.traffic_usage()

    def generate_new_mac(self):
        mac = [ 0x00, 0x16, 0x3e,
                random.randint(0x00, 0x7f),
                random.randint(0x00, 0xff),
                random.randint(0x00, 0xff) ]

        return ':'.join(map(lambda x: "%02x" % x, mac))

    def generate_new_hostname(self):
        random_string = str(uuid.uuid4())
        random_string = random_string.upper()
        random_string = random_string.replace("-", "")

        return random_string[0:10]

    def run(self):
        self.logger.info("Starting WIFIonICE Daemon")

        while True:
            traffic_usage = self.traffic_usage() - self.init_usage

            self.logger.debug("Checking Traffic Usage, {used}/{available} MB traffic used".format(
                used=traffic_usage,
                available=self.TRAFFIC_LIMIT
            ))

            if traffic_usage >= self.init_usage:
                self.logger.info("Traffic Usage exeeded. Reconnecting now...")
                self.reconnect()

            time.sleep(5)


if __name__ == '__main__':
    # Command line stub for debugging. You can directly call this script for
    # debugging purposes. Always sets the DEBUG log level and does not write
    # to a log file.

    logging.basicConfig(
        stream=sys.stdout,
        format="%(levelname)s - %(name)s -> %(message)s",
        level=logging.DEBUG)

    if not platform.system() == 'Darwin':
        print("This script does only support Mac OS X right now.")
        sys.exit(1)

    if not getpass.getuser() == 'root':
        print("Please run this script as root.")
        sys.exit(1)

    ice = WIFIonICE()
