import sys, os, time, signal, tempfile
import subprocess
from multiprocessing import Process, Queue
import simplejson as json
from socket import socket, AF_INET, SOCK_DGRAM

# Test Harness for Phantom

# Goal:
# Test two Phantom instances by performing the following steps:
# 0) Launch two Phantom instances
# 1) Open a connection from one to the other
# 2) Send UDP data to the test port of the first instance and receive on test port of the other
# 3) Send UDP data to both instances at the same time and receive on opposite ends
# 4) Report statistics
# 5) Stop Phantom instances
#
# Implementation
# We use two subprocesses to connect to the two Phantom instances' test ports

def tx_pipe(pipe_name, queue, num_msg, rate):
    fifo = os.open(pipe_name, os.O_RDWR)
    
    for i in range(0, num_msg):
        print "i=", i
        data = "hello "+str(i)
        os.write(fifo, data)
        time.sleep(rate)
    
    os.close(fifo)
    print "txDataFifo: finished"

def rx_pipe(pipe_name, queue):
    print "rxDataFifo: reading from pipe"
    fifo = os.open(pipe_name, os.O_RDWR)
    while True:
        data = os.read(fifo, 100)
        print 'rxDataFifo:', data
        queue.put(data)
    os.close(fifo)
    print "txDataFifo: reading from pipe"
        

def run_subprocess(args):
    # NOTE: Commented out parameters are like that so stdout/stderr from
    # subprocess go to shell of the main process
    p = subprocess.call(args, 
                        # stdout=subprocess.PIPE, 
                        # stderr=subprocess.STDOUT, 
                        close_fds=True, 
                        shell=True
                        )

def main():
    print "Starting test harness..."
    
    # Create pipes for each process we want to launch
    tmpdir = tempfile.mkdtemp()
    pipe0 = os.path.join(tmpdir, 'pipe0')
    pipe1 = os.path.join(tmpdir, 'pipe1')
    try:
        os.mkfifo(pipe0)
        os.mkfifo(pipe1)
    except OSError, e:
        print "Failed to create FIFO: %s" % e
    
    # handle ctrl+c and remove open files
    def signal_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        # remove all files
        try:
            filelist = [ f for f in os.listdir(tmpdir) ]
            for f in filelist: os.remove(tmpdir+'/'+f)
            # remove dir
            os.rmdir(tmpdir)
        except:
            print "unable to remove temporary directory/files:", tmpdir
        print "attempt sys.exit()"
        # sys.exit() # This doesn't do anything
        # os._exit(0) # This stops program, but doesn't kill subprocesses
        # print "sys.exit() didn't work"
            
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create list of args for each process
    phantom_path = os.getcwd() + '/' + 'phantom.py'
    args0 = [sys.executable, phantom_path, '-p', '7000', '-u', '9000', '-f', pipe0]
    args1 = [sys.executable, phantom_path, '-p', '7001', '-u', '9001', '-f', pipe1]
    
    # 0) Start phantom instances
    p0 = Process(target=run_subprocess, args=(' '.join(args0),))
    p1 = Process(target=run_subprocess, args=(' '.join(args1),))
    p0.start()
    p1.start()

    # Give them time to get up and running
    time.sleep(1)
    print "------------------------------------------------"
    print "Phantom instances started..."
    
    # 1) Open a tunnel between instances
    # Make an HTTP request to first instance to open connection to second
    import urllib2
    res = urllib2.urlopen("http://localhost:7000/open/127.0.0.1:9001").read()
    data = json.loads(res)
    if ('address' in data and 'port' in data):
        print "Phantom instances connected via tunnel"
    else:
        raise Exception('Unable to connect Phantom instances via tunnel')
    
    # 2) Send UDP data in one direction over tunnel
    time.sleep(1)
    print "------------------------------------------------"
    print "Sending data one way over tunnel..."
    
    queue = Queue() # this where output goes
    num_msg = 20 # number of messages to send over tunnel
    rate = 0.025
    p_tx = Process(target=tx_pipe, args=(pipe0, queue, num_msg, rate))
    p_rx = Process(target=rx_pipe, args=(pipe1, queue))
    p_rx.start()
    p_tx.start()
    time.sleep(1)
    p_tx.join()
    p_rx.terminate() # cannot join bc it uses while True:
    
    # Compile statistics on data transfer
    # NOTE: This totally sucks. The pipe doesn't transfer data correctly, or the
    # select() in the server process isn't pulling data off and sending it, or
    # something like that.
    recv_count = 0
    while not queue.empty():
        recv_count += 1
        data = queue.get()
    
    recv_percentage = (float(recv_count) / num_msg) * 100
    print "------------------------------------------------"
    print "One-way tunnel data transfer"
    print "Sent "+str(num_msg)+" messages at "+str(rate)+"s interval"
    print "Received "+str(recv_count)+" messages ("+str(recv_percentage)+"% success)"
    print "------------------------------------------------"
    
    # 5) Kill subprocesses
    # TODO: This doesn't work at all; the subprocesses stay alive when you
    # kill the program programmatically. CTRL+C from command line is the only
    # thing that works. See my Stackoverflow question for more:
    # http://stackoverflow.com/questions/17383917/python-program-with-subprocesses-terminates-subprocesses-on-ctrlc-but-not-on-sy

if __name__ == '__main__':
    main()


