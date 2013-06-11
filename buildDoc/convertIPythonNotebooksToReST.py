#! /usr/bin/env python

import os
import re
import subprocess
import sys
from music21 import common


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

    rstFileName = notebookFileNameWithoutExtension + '.rst'
    rstFilePath = os.path.join(
        notebookParentDirectoryPath,
        rstFileName,
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
        # Otherwise, nothing special to do, just add the line to our results:
        else:
            newLines.append(currentLine)
            currentLineNumber += 1

    with open(rstFilePath, 'w') as f:
        f.write('\n'.join(newLines))

    return rstFileName, imageFileDirectoryName


def convertAllNotebooks():
    rstDirectoryPath = common.getBuildDocRstFilePath()
    notebookDirectoryPath = os.path.join(
        common.getBuildDocFilePath(),
        'ipythonNotebooks',
        )
    for notebookFileName in [x for x in os.listdir(notebookDirectoryPath) \
        if x.endswith('.ipynb')]:
        notebookFilePath = os.path.join(
            notebookDirectoryPath, 
            notebookFileName,
            )
        rstFileName, imageFileDirectoryName = convertOneNotebook(notebookFilePath)

        oldRstFilePath = os.path.join(
            notebookDirectoryPath, 
            rstFileName,
            )
        newRstFilePath = os.path.join(
            rstDirectoryPath, 
            rstFileName,
            )
        os.rename(oldRstFilePath, newRstFilePath)

        oldImageFileDirectoryPath = os.path.join(
            notebookDirectoryPath,
            imageFileDirectoryName,
            )
        # Remove all unnecessary *.text files.
        for fileName in os.listdir(oldImageFileDirectoryPath):
            if fileName.endswith('.text'):
                filePath = os.path.join(
                    oldImageFileDirectoryPath,
                    fileName,
                    )
                os.remove(filePath)
        newImageFileDirectoryPath = os.path.join(
            rstDirectoryPath,
            imageFileDirectoryName,
            )
        # Only move the image folder if it will not overwrite anything.
        if not os.path.exists(newImageFileDirectoryPath):
            os.rename(oldImageFileDirectoryPath, newImageFileDirectoryPath)
        # Otherwise, copy its contents and delete the emptied folder.
        else:
            for fileName in os.listdir(oldImageFileDirectoryPath):
                oldFilePath = os.path.join(
                    oldImageFileDirectoryPath,
                    fileName,
                    )
                newFilePath = os.path.join(
                    newImageFileDirectoryPath,
                    fileName,
                    )
                os.rename(oldFilePath, newFilePath)
            os.remove(oldImageFileDirectoryPath)


if __name__ == '__main__':
    convertAllNotebooks()

