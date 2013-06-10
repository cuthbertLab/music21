import os
import re
import subprocess
import sys


def convertOneNotebook(notebookFilePath):
    assert os.path.exists(notebookFilePath)

    nbconvertCommand = "nbconvert.py rst {0}".format(notebookFilePath)
    subprocess.call(nbconvertCommand, shell=True)

    notebookFileNameWithoutExtension = os.path.splitext(
        os.path.basename(notebookFilePath))[0]

    notebookParentDirectoryPath = os.path.abspath(
        os.path.dirname(notebookFilePath),
        )

    imageFileDirectoryName = notebookFileNameWithoutExtension + '_files'

    rstFilePath = os.path.join(
        notebookParentDirectoryPath,
        notebookFileNameWithoutExtension + '.rst',
        )

    with open(rstFilePath, 'r') as f:
        oldLines = f.read().splitlines()

    ipythonPromptPattern = re.compile('^In\[\d+\]:')

    newLines = []
    currentLineNumber = 0
    while currentLineNumber < len(oldLines):
        currentLine = oldLines[currentLineNumber]
        # Remove all IPython prompts and the blank line that follows:
        if ipythonPromptPattern.match(currentLine) is not None:
            currentLineNumber += 2
            continue
        # Correct the image path in each ReST image directives:
        elif currentLine.startswith('.. image:: '):
            imageFileName = currentLine.partition('.. image:: ')[2]
            newImageDirective = '.. image:: {0}/{1}'.format(
                imageFileDirectoryName,
                imageFileName,
                )
            newLines.append(newImageDirective)
            currentLineNumber += 1
        # Otherwise, just add the line:
        else:
            newLines.append(currentLine)
            currentLineNumber += 1

    with open(rstFilePath, 'w') as f:
        f.write('\n'.join(newLines))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(0)
    notebookFilePath = os.path.abspath(sys.argv[1])
    convertOneNotebook(notebookFilePath)
