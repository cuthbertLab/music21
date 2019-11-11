# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         alpha/analysis/testFiles.py
# Purpose:      consolidated testFiles
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
import os
import inspect

pathName = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

K525_short_dir = pathName + os.sep + 'testfiles' + os.sep + 'K525'
K525_short_midi_path = K525_short_dir + os.sep + 'k525short_midi_ms_parsed.xml'
K525_short_omr_path = K525_short_dir + os.sep + 'k525short_omr_ms_parsed.xml'

K160_mvmt_i_path = pathName + os.sep + 'testfiles' + os.sep + 'K160'
K160_mvmt_i_midi_ms_path = K160_mvmt_i_path + os.sep + 'k160_i_midi_ms_final.xml'
K160_mvmt_i_midi_ss_path = K160_mvmt_i_path + os.sep + 'k160_i_midi_ss_final.xml'
K160_mvmt_i_omr_path = K160_mvmt_i_path + os.sep + 'k160_i_omr_ss_final.xml'
