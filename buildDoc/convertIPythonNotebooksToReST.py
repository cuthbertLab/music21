import os
import re
import subprocess
import sys


def runNBConvert(notebookFilePath):
    import music21
    pathParts = music21.__path__ + [
        'ext',
        'nbconvert',
        'nbconvert.py',
        ]
    nbconvertPath = os.path.join(*pathParts)
    nbconvertCommand = '{executable} rst {notebook}'.format(
        executable=os.path.relpath(nbconvertPath),
        notebook=os.path.relpath(notebookFilePath),
        )
    print nbconvertCommand
    subprocess.call(nbconvertCommand, shell=True)


def convertOneNotebook(notebookFilePath):
    assert os.path.exists(notebookFilePath)

    runNBConvert(notebookFilePath)

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
        # Correct the image path in each ReST image directive:
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
