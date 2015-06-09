#!/usr/bin/env python
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
import argparse

READ_BUFF_SIZE=8192

def RepresentsInt(s):
  try: 
      int(s)
      return True
  except ValueError:
      return False

class VideoHubClient(asyncore.dispatcher):
  def __init__(self, host, port = 9990,interactive=True,confirm=True,setroute="",verbose=False):
    asyncore.dispatcher.__init__(self)

    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    self.connect((host, port))

    self.is_init = False
    self.interactive = interactive
    self.confirm = confirm
    self.setroute = setroute
    self.verbose = verbose
    # Device informations
    self.protocol_version = "?"     # Protocol Preamble
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

    # write buffer
    self.buffer=''
    # pre-confirmation buffer
    self.prebuffer=''

  def handle_connect(self):
   print "Connected"
   pass
  def handle_close(self):
   print "handle_close"
   self.close()
   pass

  def serve_forever(self):
    asyncore.loop(count = 100)

  def confirm_action(self):
    if len(self.prebuffer) > 0:
      self.buffer = self.prebuffer
      self.prebuffer = ''

  def cancel_action(self):
    if len(self.prebuffer) > 0:
      print "action cancelled"
      self.prebuffer = ''

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

  def change_route(self, route_input, route_output):
     route_input = str(route_input)
     route_output = str(route_output)
     if not RepresentsInt(route_input):
       for key in self.input_labels:
          if self.input_labels[key] == route_input:
             route_input = key
             break
     if not RepresentsInt(route_output):
       for key in self.output_labels:
          if self.output_labels[key] == route_output:
             route_output = key
             break
     if not( str(route_input) in self.input_labels):
        print "There is no input:%s" % route_input
        return False
     if not( str(route_output) in self.output_labels):
        print "There is no output:%s" % route_output
        return False
     print "Route ", self.input_labels[str(route_input)], " to ", self.output_labels[str(route_output)]
     cmd = "VIDEO OUTPUT ROUTING:\n%s %s\n\n" % (str(route_output), str(route_input))
     if self.confirm:
        print "type yes to confirm, anything else to discard"
        self.prebuffer = cmd
     else:
        self.buffer = cmd

  def change_input_label(self, input_number, input_label):
     if not(str(input_number) in self.input_labels):
       print "There is no input:%s" % input_number
       return False 
     cmd = "INPUT LABELS:\n%i %s\n\n" % (int(input_number), input_label)
     if self.confirm:
        print "type yes to confirm, anything else to discard"
        self.prebuffer = cmd
     else:
        self.buffer = cmd

  def change_output_label(self, output_number, output_label):
     if not(str(output_number) in self.output_labels):
       print "There is no output:%s" % output_number
       return False 
     cmd = "OUTPUT LABELS:\n%i %s\n\n" % (int(output_number), output_label)
     if self.confirm:
        print "type yes to confirm, anything else to discard"
        self.prebuffer = cmd
     else:
        self.buffer = cmd

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

  def handle_write(self):
   sent = self.send(self.buffer)
   self.buffer = self.buffer[sent:]

  def writable(self):
   return (len(self.buffer) > 0)

class CmdlineClient(asyncore.file_dispatcher):
  def __init__(self, videohub, file):
    asyncore.file_dispatcher.__init__(self, file)
    self.videohub = videohub

  def handle_read(self):
    message = self.recv(1024)
    #print "Read keyboard read:", message
    message=message.strip(" \n")
    if message == "yes":
       self.videohub.confirm_action()
       return
    self.videohub.cancel_action()
    if message.startswith("help"):
       print "Commands:"
       print "show routing              : current routing table"
       print "show status               : device information"
       print "show inputs               : list of inputs labels"
       print "show outputs              : list of output labels"
       print "route <input> to <output> : change routing. <input> and <output> are integers or labels"
       print "set input label <input> to <Label> : change input label. <input> is 0-indexed integer"
       print "set output label <output> to <Label> : change output label. <output> is 0-indexed integer"
    elif message.startswith("show routing"):
       self.videohub.print_routing()
    elif message.startswith("show status"):
       self.videohub.print_status()
    elif message.startswith("show inputs"):
       self.videohub.print_inputs()
    elif message.startswith("show outputs"):
       self.videohub.print_outputs()
    elif message.startswith("route "):
       message_direction = message[6:]
       directions = message_direction.split(' to ')
       if len(directions) != 2:
            print "Invalid direction:", message_direction
       else:
            self.videohub.change_route(directions[0].strip(), directions[1].strip())
    elif message.startswith("set input label "):
       message_direction = message[16:]
       directions = message_direction.split(' to ')
       if len(directions) != 2:
            print "Invalid set label target:", message_direction
       else:
            self.videohub.change_input_label(directions[0].strip(), directions[1].strip())
    elif message.startswith("set output label "):
       message_direction = message[17:]
       directions = message_direction.split(' to ')
       if len(directions) != 2:
            print "Invalid set label target:", message_direction
       else:
            self.videohub.change_output_label(directions[0].strip(), directions[1].strip())
    elif len(message) <= 1:
       pass
    else:
       print "Unknown command:", message, "."

  def serve_forever(self):
    asyncore.loop(count = 100)


def main():
  verbose=False
  interactive=True
  confirm=True
  setroute=""

  parser =argparse.ArgumentParser(description='Parameters for videohubclient')
  parser.add_argument("-v","--verbose", default=False, required=False,help="Verbose mode",action="store_true")
  parser.add_argument("--nointeractive",  required=False, default=False, help="Non-interactive mode",action="store_true")
  parser.add_argument("--noconfirm",  required=False, default=False, help="Do not confirm changes",action="store_true")
  parser.add_argument("--host", required=True,help="VideoHub Hostname[:port]")
  parser.add_argument("--setroute", required=False, default="", help="'<input> to <output>'. Implies noconfirm and nointeractive")
  args = parser.parse_args()

  if args.verbose:
    verbose=True
  if args.nointeractive:
   interactive=False
   confirm=False
  if args.noconfirm:
   confirm=False
  if len(args.setroute) > 0:
   confirm=False
   interactive=False
   setroute=args.setroute

  input_line = args.host.split(':',1)
  if len(input_line) == 2:
     port = int(input_line[1])
     host = input_line[0]
  else:
     host = args.host
     port = 9990
  
  if len(args.setroute) > 0:
    directions = args.setroute.split(' to ')
    if len(directions) != 2:
        sys.stderr.write("Invalid direction:", args.setroute)
        sys.exit(1)
  else:
    directions = []
  videohub = VideoHubClient(host=host, port =port, interactive=interactive,confirm=confirm,verbose=verbose)
  cmdline = CmdlineClient(videohub=videohub, file=sys.stdin)
  iter_count = 0
  order_sent = False
  while(True):
    iter_count+=1
    videohub.serve_forever()
    if interactive:
       cmdline.serve_forever()
    if (iter_count > 1000 ) and ( videohub.device_present == False):
       sys.stderr.write("Timeout connecting to %s" % (args.host))
       sys.exit(2)
    if (iter_count > 1000 ) and videohub.device_present and not(interactive):
       break
    if (iter_count > 100 ) and videohub.device_present and len(directions) == 2 and not(order_sent):
        videohub.change_route(directions[0].strip(), directions[1].strip())
        order_sent = True

if __name__ == '__main__':
  main() 
