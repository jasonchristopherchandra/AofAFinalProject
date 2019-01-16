import sys
import time

class LZ77:
    def __init__(self):
        pass

    def filename_validation(self,filename):
        if '.' in filename:
            return True

        return False

    def append_filename(self, filename, string):
        if '.' in filename:
            i = filename.index('.')
            filename = filename[:i] + string + filename[i:]
        else:
            filename += string

        return filename

    def copy(self, data, start, end):
        length = len(data) - start
        ret_data = []

        for i in range(0, end - start):
            ret_data.append(data[start:len(data)][i % length])

        return ret_data

    def file_to_list(self, filename):
        # Read data from input file, store it in a list and then close

        data = []
        file_input = open(filename, 'rb')

        while True:
            byte = file_input.read(1)
            if not byte:
                break
            data.append(byte)

        file_input.close()
        return data

    def output_write(self, filename, data):
        # Writes every element from a list of bytes to a file

        file_output = open(filename, 'wb')

        for byte in data:
            file_output.write(byte)
        file_output.close()

    def CommonSubseq_length(self, sequence_1, sequence_2):
        i = 0
        while i < len(sequence_1) and i < len(sequence_2):
            if not sequence_1[i] == sequence_2[i]:
                break
            i += 1

        return i

    def longest_prefix(self, data, position, win_size, pv_size):
        start = 0 + (position > win_size) * (position - win_size)
        longest_start = start
        longest_length = 0

        if position + pv_size < len(data):
            end = position + pv_size
        else:
            end = len(data)

        index = start
        while index < position:
            commonseq_length = self.CommonSubseq_length(data[index:end], data[position:end])

            if commonseq_length > longest_length:
                longest_length = commonseq_length
                longest_start = abs(position - index)

            index += 1

        return longest_start, longest_length

    def compress(self, data):
        space_var = int()
        compressed_data = []
        literal_mode = {'status': False, 'position': 0}

        # The index of this loop indicates the position of the sliding window.  Everything before
        # the index is already compressed and everything after is uncompressed.

        index = 0

        while index < len(data):
            longest_start, longest_length = self.longest_prefix(data, index, 127, 10)

            # When the length of the longest sequence of data that can be compressed is less than
            # three bytes, it's not worth it to compress this sequence since compression adds two
            # bytes of overhead.  In this case, the better option is to turn on 'literal mode' and
            # keep adding the next byte to the compressed data until a sequence is found that is
            # worth compressing.

            if longest_length < 3:
                if literal_mode['status'] == True:

                    # If literal mode is already on, get the current length of the literal sequence
                    # and add one since one byte is about to be added

                    literal_length = int.from_bytes(compressed_data[literal_mode['position']], byteorder='big')
                    literal_length += 1

                    compressed_data[literal_mode['position']] = literal_length.to_bytes(1, byteorder='big')
                    compressed_data.append(data[index])

                    # Exit literal mode if the maximum length has been reached.  If the next byte
                    # is still supposed to be part of a literal sequence, a new literal sequence
                    # will have to be started

                    if compressed_data[literal_mode['position']] == 255:
                        literal_mode['status'] = False
                else:
                    # When literal mode is first turned on, one byte is added to the beginning of the
                    # sequence.  The highest order bit indicates that literal mode is on, and the
                    # remaining seven bits encode the length of the literal bytes to follow

                    compressed_data.append((129).to_bytes(1, byteorder='big'))
                    compressed_data.append(data[index])

                    literal_mode['status'] = True
                    literal_mode['position'] = len(compressed_data) - 2

                # When literal mode is on, only one byte will be added to the compressed data
                # on each iteration
                index += 1
            else:
                # Set the next_byte variable equal to the next byte in the data
                # list that comes after the data to be added to the dictionary.
                # If the index of this byte is past the end of the list, set
                # next_byte equal to the end character instead.  The end character
                # is '$' which has the decimal value 36 in UTF-8 encoding.

                if index + longest_length < len(data):
                    next_byte = data[index + longest_length]
                else:
                    next_byte = (36).to_bytes(1, byteorder='big')

                # Append the compressed data to the comp_data list

                compressed_data.append(longest_start.to_bytes(1, byteorder='big'))
                compressed_data.append(longest_length.to_bytes(1, byteorder='big'))
                compressed_data.append(next_byte)

                # If literal mode was on, turn it off

                literal_mode['status'] = False

                # Since longest_len+1 bytes were just added to the compressed data,
                # advance the list index ahead by that many bytes

                index += longest_length + 1

        space_var += (sys.getsizeof(compressed_data) + sys.getsizeof(literal_mode) + sys.getsizeof(index) + sys.getsizeof(longest_start) +
                      sys.getsizeof(longest_length) + sys.getsizeof(literal_length) + sys.getsizeof(next_byte))

        return compressed_data, space_var

    def decompress(self, data):
        space_var = int()
        decompressed_data = []
        literal_mode = {'status': False, 'length': 0}
        index = 0

        while index < len(data):
            if literal_mode['status'] == True:

                # If literal mode is on, simply append the next byte onto the
                # decompressed data list. Decrement the count of remaining
                # literal bytes in this sequence by one

                decompressed_data += [data[index]]
                literal_mode['length'] -= 1
                index += 1

                # If there are no remaining literal bytes in this sequence, exit
                # literal mode

                if literal_mode['length'] == 0:
                    literal_mode['status'] = False

            else:
                parameter_start = int.from_bytes(data[index], byteorder='big')

                if parameter_start > 128:

                    # If the first bit of the parameter start is on, the other
                    # seven bits encode the length of the literal bytes to follow

                    literal_mode['status'] = True
                    literal_mode['length'] = parameter_start - 128

                    index += 1
                else:
                    parameter_length_copy = int.from_bytes(data[index + 1], byteorder='big')

                    start = len(decompressed_data) - parameter_start
                    end = start + parameter_length_copy

                    # Copy data onto the end of the decomp list from the dictionary, which is
                    # made up of data that was previously decompressed.  Also add the next
                    # byte onto the end of the list as long as it's not the end character ('$').

                    # If one or more '$' characters were part of the actual compressed data,
                    # distinguish them from the end character by checking the value of the
                    # loop index to see if it's at the end of the compressed data or not

                    decompressed_data += self.copy(decompressed_data, start, end) + [((not data[index + 2] == b'$') or (index < len(data) - 3)) * data[index + 2]]

                    index += 3

        space_var += (sys.getsizeof(decompressed_data) + sys.getsizeof(literal_mode) + sys.getsizeof(index) +
                      sys.getsizeof(parameter_start) + sys.getsizeof(parameter_length_copy) + sys.getsizeof(start) + sys.getsizeof(end))

        return decompressed_data, space_var

class LZW:
    def __init__(self):
        pass

    def create_dict(self, mode='c-'): #function to initialize dictionary with 256 ascii characters paired with their index as their code
        if mode == 'c-':
            dictionary = dict()
            for code in range(256):
                dictionary[chr(code)] = code
            return dictionary
        elif mode == 'd-':
            dictionary = list()
            for code in range(256):
                dictionary.append(chr(code))
            return dictionary

    def compress(self, input_file, output_file): #function for compressing
        dictionary = self.create_dict()
        temp_string = str()
        code = int()
        temp_list = list()
        temp_char = str()
        space_var = int() #variable for counting space complexity
        normal_size = int() #variable for counting normal size of the file
        compressed_size = int() #variable for counting compressed size of the file
        encoded_file = open(output_file, 'wb')

        with open(input_file, 'r') as data_file:
            temp_char = data_file.read(1)

            while temp_char:
                normal_size += 1
                temp_string += temp_char

                if len(dictionary) >= 65536: #because we use 2 bytes (16 bit) size of number for the code, therefore
                    del dictionary           #there can only be 65536 of max code. if dictionary reaches 65k entries, it will reset
                    dictionary = self.create_dict()

                if temp_string not in dictionary:
                    code = len(dictionary)
                    dictionary[temp_string] = code #insert the string to the dictionary along with the code
                    temp_list = list(temp_string)
                    del temp_list[-1]
                    temp_string = "".join(temp_list) #delete the last character from the string
                    encoded_file.write(dictionary[temp_string].to_bytes(2, byteorder='big', signed=False)) #write the string to the file
                    compressed_size += 2
                    temp_string = temp_char #use the last character (the deleted one) as the next string
                temp_char = data_file.read(1) #read new character from the source

            if temp_string:
                encoded_file.write(dictionary[temp_string].to_bytes(2, byteorder='big', signed=False)) #if there is still string left,
                compressed_size += 2                                                                   #write it to the file

        encoded_file.close()
        space_var += (sys.getsizeof(dictionary) + sys.getsizeof(temp_string) + sys.getsizeof(code) + sys.getsizeof(temp_list) + sys.getsizeof(temp_char))
        return space_var, normal_size, compressed_size #calculating the space complexity by calculating all the space used for every variable

    def decompress(self, input_file, output_file): #function for decompressing
        dictionary = self.create_dict('d-')
        temp_string = str()
        code = int()
        space_var = int()
        decoded_file = open(output_file, 'w')

        with open(input_file,'rb') as encoded_file:
            code = int.from_bytes(encoded_file.read(2), byteorder='big', signed=False) #read 2 bytes from the file, and convert it to int

            while code:
                if code > len(dictionary): #because the dictionary is built incrementally along with reading the compressed file,
                    raise IndexError("Out of range index, invalid code") #if there is code that values above the current length of the dictionary
                                                                         #that means, the file is corrupted
                if len(dictionary) >= 65536:
                    del dictionary #resetting the dictionary after it reaches 65536 (max value of our code)
                    dictionary = self.create_dict('d-')

                if code == len(dictionary): #if the code's value is the same as the dictionary's length (not yet exists)
                    dictionary.append(temp_string + temp_string[0]) #it will append the string combined with the first character of the same string to the dictionary
                elif temp_string: #if not, that means the code is below the current length (exists in the dictionary)
                    dictionary.append(temp_string + dictionary[code][0]) #it will append the string combined with the first character of the string which the code refers to to the dictionary

                decoded_file.write(dictionary[code]) #write the string which the code refers to to the file
                temp_string = dictionary[code] #use the string that the code refers to as the next string
                code = int.from_bytes(encoded_file.read(2), byteorder='big', signed=False) #read 2 bytes from the file and convert it to int

        decoded_file.close()
        space_var += (sys.getsizeof(dictionary) + sys.getsizeof(temp_string) + sys.getsizeof(code)) #calculating the space used
        return space_var

def lz77_main(lz77):
    action = input("c- for compression\nd- for decompression\n> ")
    input_file = input("Type your input file\n> ")
    output_file = input("Type your output file\n> ")
    start_time = float()
    space_var = int()

    if action == "c-":
        if output_file == '':
            output_file = lz77.append_filename(input_file, '_comp')

        start_time = time.time()
        data = lz77.file_to_list(input_file)

        # Pass data to be compressed to the compress function.  Store returned compressed data in the
        # compressed_data variable

        compressed_data, space_var = lz77.compress(data)

        # Write compressed data to output file
        lz77.output_write(output_file, compressed_data)
        space_var += sys.getsizeof(data)

        print('File successfully compressed')
        print('Compression ratio: %.2f' % float(100 - (len(compressed_data) / len(data) * 100)))
        print("Runtime: %.2f seconds" % (time.time() - start_time))
        print("Space Complexity: %d bytes" % space_var)

    elif action == "d-":
        if output_file == '':
            output_file = lz77.append_filename(input_file, '_decomp')

        start_time = time.time()
        data = lz77.file_to_list(input_file)

        # Pass data to be decompressed to the decompress function.  Store returned decompressed data in the
        # decompressed_data variable

        decompressed_data, space_var = lz77.decompress(data)

        # Write decompressed data to output file
        lz77.output_write(output_file, decompressed_data)
        space_var += sys.getsizeof(data)

        print('File successfully decompressed')
        print("Runtime: %.2f seconds" % (time.time() - start_time))
        print("Space Complexity: %d bytes" % space_var)

def lzw_main(lzw):
    start_time = float()
    space_var = int()
    normal_size = int()
    compressed_size = int()

    action = input("'c-' for compression\n'd-' for decompression\n> ")

    input_file = input("Type the input file\n> ")
    output_file = input("Type the output file\n> ")

    if action == 'c-':
        start_time = time.time()
        space_var, normal_size, compressed_size = lzw.compress(input_file, output_file)
        print('File successfully compressed')
        print('Compression ratio: %.2f' % float(100 - (compressed_size / normal_size * 100)))
        print("Runtime: %.2f seconds" % (time.time() - start_time))
        print("Space Complexity: %d bytes" % space_var)

    elif action == 'd-':
        start_time = time.time()
        space_var = lzw.decompress(input_file, output_file)
        print('File successfully decompressed')
        print("Runtime: %.2f seconds" % (time.time() - start_time))
        print("Space Complexity: %d bytes" % space_var)

algorithm = str()
lz77 = LZ77()
lzw = LZW()
while True:
    algorithm = input("Which algorithm do you want to use?\n1. LZ77\n2. LZW\n3. Exit\n> ")
    if algorithm == '1':
        lz77_main(lz77)
    elif algorithm == '2':
        lzw_main(lzw)
    elif algorithm == '3':
        sys.exit()
        
     
#References:
#http://www.cplusplus.com/articles/iL18T05o/#LossCoVsExp
#http://warp.povusers.org/EfficientLZW/index.html
#https://github.com/mckasza/mk_compress
