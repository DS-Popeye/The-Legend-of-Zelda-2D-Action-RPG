import pygame
from settings import *
from random import randint

class MagicPlayer:
	def __init__(self,animation_player):
		self.animation_player = animation_player
		self.sounds = {
			'heal': pygame.mixer.Sound('../audio/heal.wav'),
			'flame': pygame.mixer.Sound('../audio/Fire.wav')
		}

	def heal(self,player,strength,cost,groups):
		if player.energy >= cost:
			player.energy -= cost
			player.health += strength

			if player.health > player.max_stats['health']:  # ✅ FIX
				player.health = player.max_stats['health']

			self.sounds['heal'].play()
			self.animation_player.create_particles('aura',player.rect.center,groups)
			self.animation_player.create_particles('heal',player.rect.center,groups)

	def flame(self,player,cost,groups):
		if player.energy >= cost:
			player.energy -= cost
			self.sounds['flame'].play()

			direction = pygame.math.Vector2()
			if player.status.startswith('right'): direction.x = 1
			elif player.status.startswith('left'): direction.x = -1
			elif player.status.startswith('up'): direction.y = -1
			else: direction.y = 1

			for i in range(1,6):
				offset = direction * i * TILESIZE
				pos = player.rect.center + offset
				self.animation_player.create_particles('flame',pos,groups)
