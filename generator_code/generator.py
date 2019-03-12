# Copyright 2019 The Magenta Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

##
## Code modified by Ilann Adjedj for emlyon makerslab
##

# Libraries

import os
import random

import pandas as pd
from watson_developer_cloud.natural_language_understanding_v1 import *

import magenta
from magenta.models.performance_rnn import performance_model
from magenta.models.performance_rnn import performance_sequence_generator
from magenta.music import constants
from magenta.music import performance_controls
from magenta.music import midi_io
from magenta.protobuf import generator_pb2
from magenta.protobuf import music_pb2
import tensorflow as tf

import music21

# Constant and parameters

# These are the 12 most commons categories in the Scripta file, you can use
# other categories depending on your dataset
cat_map = {
	"business and industrial" : 0,
	"education" : 1,
	"finance" : 2,
	"technology and computing" : 3,
	"automotive and vehicles" : 4,
	"health and fitness" : 5,
	"law govt and politics" : 6,
	"science" : 7,
	"society" : 8,
	"real estate" : 9,
	"news" : 10,
	"careers" : 11
}

# Globals

pitch_class_histogram = []
num_steps = 0
notes_per_second = "0.0"

## Replace here with your credentials

tone_analyzer = NaturalLanguageUnderstandingV1(
	url='https://gateway-lon.watsonplatform.net/natural-language-understanding/api',
	version='2017-09-21',
	iam_apikey='REPLACE WITH YOUR API KEY HERE')

# Import scripta CSV file
data = pd.read_csv('input.csv')
data = data.head(2).copy() #uncomment for testing on only a small batch

def remap(x, in_min, in_max, out_min, out_max):
	return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def rotateArray(l, n):
		return l[n:] + l[:n]

def make_pitch_histogram(sentiment, category):
	if sentiment > 0.5:
		array = [5,0,1,0,2,2,0,3,0,1,0,1] # major scale
	elif sentiment >= 0:
		array = [5,0,1,0,3,0,0,4,0,4,0,0] # major pentatonic
	elif sentiment >= -0.5:
		array = [5,0,0,3,0,3,0,5,0,0,4,0] # minor pentatonic
	else:
		array = [5,0,1,2,0,2,0,3,1,0,0,1] # minor scale

	try:
		array = rotateArray(array, 12 - cat_map[category])
	except KeyError as e:
		array = rotateArray(array, random.randrange(12))

	return str(array)

def run_with_flags(generator, filename):
	global pitch_class_histogram, num_steps, notes_per_second

	primer_sequence = music_pb2.NoteSequence()
	primer_sequence.ticks_per_quarter = 96

	# Derive the total number of seconds to generate.
	seconds_per_step = 1.0 / generator.steps_per_second
	generate_end_time = num_steps * seconds_per_step

	# Specify start/stop time for generation based on starting generation at the
	# end of the priming sequence and continuing until the sequence is num_steps
	# long.
	gen_options = generator_pb2.GeneratorOptions()
	# Set the start time to begin when the last note ends.
	generate_section = gen_options.generate_sections.add(
			start_time=primer_sequence.total_time,
			end_time=generate_end_time)

	gen_options.args['temperature'].float_value = 1.0
	gen_options.args['beam_size'].int_value = 1
	gen_options.args['branch_factor'].int_value = 1
	gen_options.args['steps_per_iteration'].int_value = 1
	gen_options.args['notes_per_second'].string_value = notes_per_second
	gen_options.args['pitch_class_histogram'].string_value = pitch_class_histogram

	generated_sequence = generator.generate(primer_sequence, gen_options)

	magenta.music.sequence_proto_to_midi_file(generated_sequence, filename)
	
	# Generated music tends to be super fast and messy so we slow them by half
	score = music21.converter.parse(filename)
	new_score = score.scaleOffsets(2).scaleDurations(2)
	new_score.write('midi', filename) 

def main():
	bundle = magenta.music.read_bundle_file("./multiconditioned_performance_with_dynamics.mag")
	
	config_id = bundle.generator_details.id
	config = performance_model.default_configs[config_id]

	generator = performance_sequence_generator.PerformanceRnnSequenceGenerator(
			model=performance_model.PerformanceRnnModel(config),
			details=config.details,
			steps_per_second=config.steps_per_second,
			num_velocity_bins=config.num_velocity_bins,
			control_signals=config.control_signals,
			optional_conditioning=config.optional_conditioning,
			bundle=bundle,
			note_performance=config.note_performance)

	midi_output_dir = os.path.expanduser("./generated_mid")
	if not tf.gfile.Exists(midi_output_dir):
		tf.gfile.MakeDirs(midi_output_dir)

	mp3_output_dir = os.path.expanduser("./generated_mp3")
	if not tf.gfile.Exists(mp3_output_dir):
		tf.gfile.MakeDirs(mp3_output_dir)

	## Main for loop
	## Analyse datas line by line with Watson NLU and use analysis results to generate music
	featuresOptions = Features(keywords=KeywordsOptions(),
								sentiment=SentimentOptions(),
								concepts=ConceptsOptions(limit=100),
								categories=CategoriesOptions(1))

	for index, summary in data['Summary'].iteritems():
		json_output = tone_analyzer.analyze(features=featuresOptions, text=summary)

		result = json_output.result

		print "================================================================================"
		print data.at[index, "Auteur"]
		print result["sentiment"]["document"]["score"]

		data.at[index, "len"] = len(summary)
		data.at[index, "nbkeywords"] = len(result["keywords"])
		data.at[index, "nbconcepts"] = len(result["concepts"])
		data.at[index, "category"] = result["categories"][0]["label"].split("/")[1]
		data.at[index, "sentiment"] = result["sentiment"]["document"]["score"]
		data.at[index, "filename"] = str(index) + " " + data.at[index, "Auteur"] + ".mp3"		

		global pitch_class_histogram, num_steps, notes_per_second

		pitch_class_histogram = make_pitch_histogram(data.at[index, "sentiment"],
													data.at[index, "category"])
		num_steps = remap(data.at[index, "len"], 500, 1500, 1500, 3000)
		notes_per_second = str(remap(data.at[index, "nbkeywords"],0, 50, 5, 15) / 1.0)

		filename = str(index) + " " + data.at[index, "Auteur"]
		print pitch_class_histogram
		print num_steps
		print notes_per_second
	
		midi_filename = '%s.mid' % (filename)
		midi_path = os.path.join(midi_output_dir, midi_filename)

		# Generate MIDI file with magenta
		run_with_flags(generator, midi_path)

		# Command line black magic (convert Midi to MP3)
		os.system("fluidsynth -r 44100 -R 0 -E little -T raw -O s16 -i -l -F - \
			./FreePats2-GM.sf2 ./gen_mid/" + str(index) + "\\ " + data.at[index, "Auteur"].replace(" ", "\\ ") + ".mid | \
			lame  -r --signed -s 44100 -b 320 - ./generated_mp3/" + str(index) + "\\ " + data.at[index, "Auteur"].replace(" ", "\\ ") + ".mp3")  

	# Save all datas to CSV
	data.to_csv('output.csv')

	# Format data for RPi and export to JSON
	data_for_json = data.drop(["len", "nbkeywords", "Coauteurs", "Summary", "Date","Langue" ,"nbconcepts", "category", "sentiment"], axis=1)
	data_for_json.rename(columns={"Auteur": "line1"}, inplace=True)
	data_for_json.rename(columns={"Titre": "line2"}, inplace=True)
	data_for_json.T.to_json("output.json")


if __name__ == '__main__':
	main()