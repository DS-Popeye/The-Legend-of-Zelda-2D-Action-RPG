import pygame
from settings import *
from tile import Tile
from player import Player
from support import *
from random import choice, randint
from weapon import Weapon
from ui import UI
from enemy import Enemy
from particles import AnimationPlayer
from magic import MagicPlayer
from upgrade import Upgrade


class Level:
	def __init__(self):

		self.display_surface = pygame.display.get_surface()
		self.state = 'playing'  # playing | game_over | win

		# enemy tracking
		self.total_enemies = 0
		self.enemies_killed = 0

		# sprite groups
		self.visible_sprites = YSortCameraGroup()
		self.obstacle_sprites = pygame.sprite.Group()
		self.attack_sprites = pygame.sprite.Group()
		self.attackable_sprites = pygame.sprite.Group()

		self.current_attack = None

		# setup
		self.create_map()

		# systems
		self.ui = UI()
		self.upgrade = Upgrade(self.player)
		self.animation_player = AnimationPlayer()
		self.magic_player = MagicPlayer(self.animation_player)

	def create_map(self):
		layouts = {
			'boundary': import_csv_layout('../map/map_FloorBlocks.csv'),
			'grass': import_csv_layout('../map/map_Grass.csv'),
			'object': import_csv_layout('../map/map_Objects.csv'),
			'entities': import_csv_layout('../map/map_Entities.csv')
		}

		graphics = {
			'grass': import_folder('../graphics/Grass'),
			'objects': import_folder('../graphics/objects')
		}

		for style, layout in layouts.items():
			for row_i, row in enumerate(layout):
				for col_i, col in enumerate(row):
					if col == '-1':
						continue

					x = col_i * TILESIZE
					y = row_i * TILESIZE

					if style == 'boundary':
						Tile((x, y), [self.obstacle_sprites], 'invisible')

					if style == 'grass':
						Tile(
							(x, y),
							[self.visible_sprites, self.obstacle_sprites, self.attackable_sprites],
							'grass',
							choice(graphics['grass'])
						)

					if style == 'object':
						Tile(
							(x, y),
							[self.visible_sprites, self.obstacle_sprites],
							'object',
							graphics['objects'][int(col)]
						)

					if style == 'entities':
						if col == '394':
							self.player = Player(
								(x, y),
								[self.visible_sprites],
								self.obstacle_sprites,
								self.create_attack,
								self.destroy_attack,
								self.create_magic
							)
						else:
							if col == '390':
								monster = 'bamboo'
							elif col == '391':
								monster = 'spirit'
							elif col == '392':
								monster = 'raccoon'
							else:
								monster = 'squid'

							Enemy(
								monster,
								(x, y),
								[self.visible_sprites, self.attackable_sprites],
								self.obstacle_sprites,
								self.damage_player,
								self.trigger_death_particles,
								self.add_exp
							)

							self.total_enemies += 1

	def create_attack(self):
		self.current_attack = Weapon(self.player, [self.visible_sprites, self.attack_sprites])

	def destroy_attack(self):
		if self.current_attack:
			self.current_attack.kill()
		self.current_attack = None

	def create_magic(self, style, strength, cost):
		if style == 'heal':
			self.magic_player.heal(self.player, strength, cost, [self.visible_sprites])
		elif style == 'flame':
			self.magic_player.flame(self.player, cost, [self.visible_sprites, self.attack_sprites])

	def player_attack_logic(self):
		for attack in self.attack_sprites:
			targets = pygame.sprite.spritecollide(attack, self.attackable_sprites, False)
			for target in targets:
				if target.sprite_type == 'grass':
					for _ in range(randint(3, 6)):
						self.animation_player.create_grass_particles(
							target.rect.center, [self.visible_sprites]
						)
					target.kill()
				else:
					target.get_damage(self.player, attack.sprite_type)

	def damage_player(self, amount, attack_type):
		if self.player.vulnerable:
			self.player.health -= amount
			self.player.vulnerable = False
			self.player.hurt_time = pygame.time.get_ticks()
			self.animation_player.create_particles(
				attack_type, self.player.rect.center, [self.visible_sprites]
			)

	def trigger_death_particles(self, pos, particle):
		self.animation_player.create_particles(particle, pos, self.visible_sprites)

	def add_exp(self, amount):
		self.player.exp += amount
		self.enemies_killed += 1

	def check_end_conditions(self):
		if self.player.health <= 0:
			self.state = 'game_over'
		elif self.enemies_killed >= self.total_enemies:
			self.state = 'win'

	def run(self):
		self.visible_sprites.custom_draw(self.player)
		self.ui.display(self.player, self.enemies_killed, self.total_enemies, self.state)

		if self.state == 'playing':
			self.visible_sprites.update()
			self.visible_sprites.enemy_update(self.player)
			self.player_attack_logic()
			self.check_end_conditions()


# ======================================================
# CAMERA GROUP  (THIS WAS MISSING / BROKEN BEFORE)
# ======================================================

class YSortCameraGroup(pygame.sprite.Group):
	def __init__(self):
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.half_width = self.display_surface.get_width() // 2
		self.half_height = self.display_surface.get_height() // 2
		self.offset = pygame.math.Vector2()

		self.floor_surf = pygame.image.load('../graphics/tilemap/ground.png').convert()
		self.floor_rect = self.floor_surf.get_rect(topleft=(0, 0))

	def custom_draw(self, player):
		self.offset.x = player.rect.centerx - self.half_width
		self.offset.y = player.rect.centery - self.half_height

		floor_offset = self.floor_rect.topleft - self.offset
		self.display_surface.blit(self.floor_surf, floor_offset)

		for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image, offset_pos)

	def enemy_update(self, player):
		for sprite in self.sprites():
			if hasattr(sprite, 'sprite_type') and sprite.sprite_type == 'enemy':
				sprite.enemy_update(player)
