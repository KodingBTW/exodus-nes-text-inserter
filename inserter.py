# Exodus - Journey to the Promised Land text inserter
# Source code by koda
# Version 1.0 - 28-10-2024

import sys
import os

def readTextFile(txtFile):
    """
    Reads a text file and retrieves the byte count and texts.
    
    Parameters:
        txtFile (str): The path to the text file to read.
    
    Returns:
        tuple: A tuple containing:
            - int: The total byte count from the first line of the file.
            - list: A list of strings, each representing a line of text from the file.
    """
    with open(txtFile, "r", encoding='iso-8859-1') as f:
        # Read the total byte count from the first line
        firstLine = f.readline()
        try:
            value = int(firstLine)  # Check if the first line is a integer.
        except ValueError:
            print("Text length not found.\n")
            sys.exit(1)
        # Read the remaining lines as texts
        texts = [line.strip() for line in f.readlines()]
    return value, texts

def characterReplacer(textList):
    """
    Replaces specific characters in the text based on a predefined dictionary.
    
    Parameters:
        textList (list): A list of strings to process.
    
    Returns:
        list: A new list of strings with characters replaced.
    """
    replacement_dict = {
        '?': '#',
        '¿': '$',
        'á': '%',
        'é': 'K',
        'í': 'W',
        'ó': 'X',
        'ú': 'w',
        'ñ': ')',
        'Á': "'",
        'É': '('
    }
    
    replaced_texts = []
    
    for text in textList:
        replaced_text = ''.join(replacement_dict.get(char, char) for char in text)
        replaced_texts.append(replaced_text)
    
    return replaced_texts

def encodeTextsAndPointers(texts, textStartOffset, pointersDistance):
    """
    Encodes the texts into bytes and calculates the pointers.
    
    Parameters:
        texts (list): A list of strings to encode.
        textStartOffset (int): The starting offset for the text in the ROM.
        pointersDistance (int): The distance to subtract from each pointer.
    
    Returns:
        tuple: A tuple containing:
            - bytearray: The encoded text data.
            - int: The total number of bytes encoded.
            - bytearray: The encoded pointers data.
    """
    encodedData = bytearray()  # Bytearray to store encoded data
    totalBytes = 0  # Byte counter
    pointers = [textStartOffset]  # Initialize with the startOffset as the first pointer
    
    for text in texts:
        textContent = text[:-1]  # The content of the text (without the breaker)
        breaker = text[-1:]      # The breaker (last character)

        # Encode text to bytes
        encodedData.extend(textContent.encode('utf-8', errors='ignore'))
        encodedData.extend(breaker.encode('utf-8', errors='ignore'))  # Add the breaker byte

        # Update the byte counter
        totalBytes += len(textContent.encode('utf-8', errors='ignore')) + len(breaker.encode('utf-8', errors='ignore'))

        # Calculate the pointer and add it to the list (add 1 to point to the next byte)
        pointers.append(textStartOffset + totalBytes)
        
    # Remove the last pointer generated after the last text
    pointers.pop()

    # Subtract 0x8010 from each pointer in the list
    pointers = [ptr - pointersDistance for ptr in pointers]
    pointers = [((ptr >> 8) & 0xFF) | ((ptr & 0xFF) << 8) for ptr in pointers]  # Reverse bytes

    # Convert the list of pointers to bytearray
    pointersData = bytearray()
    for ptr in pointers:
        pointersData.append((ptr >> 8) & 0xFF)  # First byte (most significant)
        pointersData.append(ptr & 0xFF)         # Second byte (least significant)
        
    return encodedData, totalBytes, pointersData


def writeROM(romFile, startOffset, data):
    """
    Writes data to the ROM at the specified offset.
    
    Parameters:
        romFile (str): The path to the ROM file.
        startOffset (int): The offset in the ROM file where data should be written.
        data (bytes or bytearray): The data to write to the ROM.
    """
    with open(romFile, "r+b") as f:  # Open in read and write binary mode
        f.seek(startOffset)
        f.write(data)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stdout.write("Usage: python <script_name.py> <txtFile.txt> <romFile.rom>\n")
        sys.exit(1)

    txtFile = sys.argv[1]  # Text file containing the strings to insert
    romFile = sys.argv[2]  # ROM file to write the data into

    # IMPORTANT OFFSETS (DON'T TOUCH)
    TEXTSTARTOFFSET = 0x1007B           # Text first offset 1007B.
    POINTERSSTARTOFFSET = 0x144F4       # Table pointers first offset 144F4.
    POINTERSDISTANCE = 0x8010           # Text offset - Inverted Pointer.

    # Read the text file
    lengthText, text = readTextFile(txtFile)
    
    # Replace characters
    replacedText = characterReplacer(text)

    # Encode the texts
    encodedData, totalBytes, pointersList = encodeTextsAndPointers(replacedText, TEXTSTARTOFFSET, POINTERSDISTANCE)

    # Check that the size of the data does not exceed the maximum allowed
    if len(encodedData) > int(lengthText):
        excess = len(encodedData) - int(lengthText)
        sys.stdout.write("ERROR: The number of bytes read exceeds the maximum block limit.\n")
        sys.stdout.write(f"Remove {excess} bytes from {txtFile} file.\n") 
        sys.exit(1)

    # Check free bytes
    freeBytes = int(lengthText) - len(encodedData)
        
    # Write the text to the ROM
    writeROM(romFile, TEXTSTARTOFFSET, encodedData)

    # Write the pointers to the ROM
    writeROM(romFile, POINTERSSTARTOFFSET, pointersList)

    print(f"Text written at offset {hex(TEXTSTARTOFFSET)}.")
    print(f"Pointers table written at offset {hex(POINTERSSTARTOFFSET)} with {len(pointersList)//2} pointers.")
    print(f"Free space: {freeBytes} bytes remaining.")
    print(f"Data written to {romFile} successfully.\n")
    
