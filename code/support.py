from csv import reader
from os import walk
import pygame


def import_csv_layout(path):
	terrain_map = []

	try:
		with open(path) as level_map:
			layout = reader(level_map, delimiter=',')
			for row in layout:
				terrain_map.append(list(row))
	except FileNotFoundError:
		print(f'[ERROR] CSV file not found: {path}')
	except Exception as e:
		print(f'[ERROR] Failed to read CSV {path}: {e}')

	return terrain_map


def import_folder(path):
	surface_list = []

	for _, __, img_files in walk(path):
		for image in img_files:
			full_path = path + '/' + image
			try:
				image_surf = pygame.image.load(full_path).convert_alpha()
				surface_list.append(image_surf)
			except pygame.error as e:
				print(f'[ERROR] Failed to load image: {full_path} -> {e}')

	return surface_list
