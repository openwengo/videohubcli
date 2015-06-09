"""
Copyright (c) 2015, Olivier Schiavo / Wengo SAS
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import asyncore, socket
import sys
import collections

READ_BUFF_SIZE=8192

class VideoHubClient(asyncore.dispatcher):
  def __init__(self, host, port = 9990):
    asyncore.dispatcher.__init__(self)
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #sock.connect((host, port))
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.connect((host, port))
    ## Init dispatcher with request
    self.is_init = False
    self.protocol_version = "?"
    self.device_present = False
    self.model_name = "?"
    self.friendly_name = "?"
    self.unique_id = "?"
    self.video_inputs = 0
    self.video_processing_units = 0
    self.video_outputs = 0
    self.video_monitoring_outputs = 0
    self.serial_ports = 0
    self.input_labels = {}
    self.output_labels = {}
    self.video_output_locks = {}
    self.video_output_routing = {}

  def handle_connect(self):
   print "Connected"
   pass
  def handle_close(self):
   print "handle_close"
   self.close()
   pass

  def serve_forever(self):
    asyncore.loop(count = 100)

  def print_status(self):
   print "Status:"
   if not self.is_init:
     print "Device is not initialized"
     return
   print "Protocol version : %-40.40s" % ( self.protocol_version )
   print "Model name       : %-40.40s" % ( self.model_name )
   print "Friendly name    : %-40.40s" % ( self.friendly_name )
     
  def print_routing(self):
    print "Routing:"
    key = lambda x: int(x[0]) 
    routing_ordered = collections.OrderedDict(sorted(self.video_output_routing.items(), key=key))
    for key in routing_ordered:
      item = self.video_output_routing[key]
      print "%3d:%-32.32s>%32.32s:%3d" % ( int(item), self.input_labels[item], self.output_labels[key], int(key) )

  def print_inputs(self):
    print "Inputs:"
    key = lambda x: int(x[0]) 
    inputs_ordered = collections.OrderedDict(sorted(self.input_labels.items(), key=key))
    for key in inputs_ordered:
      print "%3d:%-32.32s" % ( int(key), self.input_labels[key])

  def print_outputs(self):
    print "Outputs:"
    key = lambda x: int(x[0]) 
    outputs_ordered = collections.OrderedDict(sorted(self.output_labels.items(), key=key))
    for key in outputs_ordered:
      print "%3d:%-32.32s" % ( int(key), self.output_labels[key])


  def handle_read(self):
   message = ""
   while(True):
    str = self.recv(READ_BUFF_SIZE)
    message += str
    if (len(str) < READ_BUFF_SIZE):
       break
   line_array = message.split('\n')
   while(len(line_array) > 0):
     first_line = line_array.pop(0)
     #print first_line
     #print "This is a ", first_line, " message"
     if first_line == "PROTOCOL PREAMBLE:":
       if len(line_array) == 0:
          break
       current_line = line_array.pop(0)
       if current_line.startswith("Version:"):
          self.protocol_version =  current_line.split(': ')[1]
          #print "Protocol =", self.protocol_preamble
       self.is_init = True

     if first_line == "VIDEOHUB DEVICE:":
       current_line = first_line    
       while (len(line_array) > 0) and current_line != "":
         current_line = line_array.pop(0)
         if current_line.startswith("Device present: true"):
          self.device_present = True
          #print "Device Present =", self.device_present
         if current_line.startswith("Device present: false"):
          self.device_present = False
          #print "Device Present =", self.device_present
         if current_line.startswith("Model name:"):
          self.model_name =  current_line.split(': ')[1]
          #print "Model name =", self.model_name
         if current_line.startswith("Friendly name:"):
          self.friendly_name =  current_line.split(': ')[1]
          #print "Friendly name =", self.friendly_name
         if current_line.startswith("Unique ID:"):
          self.unique_id =  current_line.split(': ')[1]
          #print "Unique ID =", self.unique_id
         if current_line.startswith("Video inputs:"):
          self.video_inputs =  current_line.split(': ')[1]
          #print "Video inputs =", self.video_inputs
         if current_line.startswith("Video processing units:"):
          self.video_processing_units =  current_line.split(': ')[1]
          #print "Video processing units =", self.video_processing_units
         if current_line.startswith("Video outputs:"):
          self.video_outputs =  current_line.split(': ')[1]
          #print "Video outputs =", self.video_outputs
         if current_line.startswith("Video monitoring outputs:"):
          self.video_monitoring_outputs =  current_line.split(': ')[1]
          #print "Video monitoring outputs =", self.video_monitoring_outputs
         if current_line.startswith("Serial ports:"):
          self.serial_ports =  current_line.split(': ')[1]
          #print "Serial ports =", self.serial_ports
       self.print_status()

     if first_line == "INPUT LABELS:":
       current_line = first_line    
       while (len(line_array) > 0) and current_line != "":
         current_line = line_array.pop(0)
         input_line = current_line.split(' ',1)
         if len(input_line) == 2:
           self.input_labels[ input_line[0]] = input_line[1]
       self.print_inputs()
       #print "Input labels =", self.input_labels

     if first_line == "OUTPUT LABELS:":
       current_line = first_line    
       while (len(line_array) > 0) and current_line != "":
         current_line = line_array.pop(0)
         input_line = current_line.split(' ',1)
         if len(input_line) == 2:
           self.output_labels[ input_line[0]] = input_line[1]
       self.print_outputs()
       #print "Output labels =", self.output_labels

     if first_line == "VIDEO OUTPUT LOCKS:":
       current_line = first_line    
       while (len(line_array) > 0) and current_line != "":
         current_line = line_array.pop(0)
         input_line = current_line.split(' ',1)
         if len(input_line) == 2:
           self.video_output_locks[ input_line[0]] = input_line[1]
       #print "Video output locks =", self.video_output_locks

     if first_line == "VIDEO OUTPUT ROUTING:":
       current_line = first_line    
       while (len(line_array) > 0) and current_line != "":
         current_line = line_array.pop(0)
         input_line = current_line.split(' ',1)
         if len(input_line) == 2:
           self.video_output_routing[ input_line[0]] = input_line[1]
       self.print_routing()

class CmdlineClient(asyncore.file_dispatcher):
  def __init__(self, videohub, file):
    asyncore.file_dispatcher.__init__(self, file)
    self.videohub = videohub

  def handle_read(self):
    message = self.recv(1024)
    #print "Read keyboard read:", message
    if message.startswith("show routing"):
       self.videohub.print_routing()
    elif message.startswith("show status"):
       self.videohub.print_status()
    elif message.startswith("show inputs"):
       self.videohub.print_inputs()
    elif message.startswith("show outputs"):
       self.videohub.print_outputs()
    elif len(message) <= 1:
       pass
    else:
       print "Unknown command:", message

  def serve_forever(self):
    asyncore.loop(count = 100)


if __name__ == '__main__':
  if len(sys.argv) > 1:
    host = sys.argv[1]
  else:
    print "Usage: ", sys.argv[0], " <videohubhostname>[:port]"
    sys.exit(1)
  input_line = host.split(':',1)
  if len(input_line) == 2:
     port = int(input_line[1])
     host = input_line[0]
  else:
     port = 9990
  videohub = VideoHubClient(host=host, port =port)
  cmdline = CmdlineClient(videohub=videohub, file=sys.stdin)
  iter_count = 0
  while(True):
    iter_count+=1
    videohub.serve_forever()
    cmdline.serve_forever()
    if (iter_count > 1000 ) and ( videohub.device_present == False):
       print "Timeout connecting.."
       sys.exit(1)
