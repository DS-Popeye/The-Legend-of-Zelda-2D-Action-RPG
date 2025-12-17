import pygame
from settings import *
from support import import_folder
from entity import Entity


class Player(Entity):
	def __init__(self, pos, groups, obstacle_sprites, create_attack, destroy_attack, create_magic):
		super().__init__(groups)

		# image
		try:
			self.image = pygame.image.load('../graphics/test/player.png').convert_alpha()
		except pygame.error:
			raise SystemExit('[FATAL] Player image missing')

		self.rect = self.image.get_rect(topleft=pos)
		self.hitbox = self.rect.inflate(-6, HITBOX_OFFSET['player'])

		# graphics
		self.import_player_assets()
		self.status = 'down'

		# movement
		self.direction = pygame.math.Vector2()
		self.attacking = False
		self.attack_cooldown = 400
		self.attack_time = None
		self.obstacle_sprites = obstacle_sprites

		# weapon
		self.create_attack = create_attack
		self.destroy_attack = destroy_attack
		self.weapon_index = 0
		self.weapon = list(weapon_data.keys())[self.weapon_index]
		self.can_switch_weapon = True
		self.weapon_switch_time = None
		self.switch_duration_cooldown = 200

		# magic
		self.create_magic = create_magic
		self.magic_index = 0
		self.magic = list(magic_data.keys())[self.magic_index]
		self.can_switch_magic = True
		self.magic_switch_time = None

		# stats
		self.stats = {'health': 100, 'energy': 60, 'attack': 10, 'magic': 4, 'speed': 5}
		self.max_stats = {'health': 300, 'energy': 140, 'attack': 20, 'magic': 10, 'speed': 10}
		self.upgrade_cost = {'health': 100, 'energy': 100, 'attack': 100, 'magic': 100, 'speed': 100}

		self.health = self.stats['health'] * 0.5
		self.energy = self.stats['energy'] * 0.8
		self.exp = 5000
		self.speed = self.stats['speed']

		# damage / invulnerability
		self.vulnerable = True
		self.hurt_time = None
		self.invulnerability_duration = 500

		# sound
		try:
			self.weapon_attack_sound = pygame.mixer.Sound('../audio/sword.wav')
			self.weapon_attack_sound.set_volume(0.4)
		except pygame.error:
			print('[WARNING] sword.wav missing')
			self.weapon_attack_sound = None

	def import_player_assets(self):
		character_path = '../graphics/player/'
		self.animations = {
			'up': [], 'down': [], 'left': [], 'right': [],
			'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
			'right_attack': [], 'left_attack': [], 'up_attack': [], 'down_attack': []
		}

		for animation in self.animations.keys():
			self.animations[animation] = import_folder(character_path + animation)

	def input(self):
		if not self.attacking:
			keys = pygame.key.get_pressed()

			if keys[pygame.K_UP]:
				self.direction.y = -1
				self.status = 'up'
			elif keys[pygame.K_DOWN]:
				self.direction.y = 1
				self.status = 'down'
			else:
				self.direction.y = 0

			if keys[pygame.K_RIGHT]:
				self.direction.x = 1
				self.status = 'right'
			elif keys[pygame.K_LEFT]:
				self.direction.x = -1
				self.status = 'left'
			else:
				self.direction.x = 0

			if keys[pygame.K_SPACE]:
				self.attacking = True
				self.attack_time = pygame.time.get_ticks()
				self.create_attack()
				if self.weapon_attack_sound:
					self.weapon_attack_sound.play()

			if keys[pygame.K_LCTRL]:
				self.attacking = True
				self.attack_time = pygame.time.get_ticks()
				style = list(magic_data.keys())[self.magic_index]
				strength = list(magic_data.values())[self.magic_index]['strength'] + self.stats['magic']
				cost = list(magic_data.values())[self.magic_index]['cost']
				self.create_magic(style, strength, cost)

			if keys[pygame.K_q] and self.can_switch_weapon:
				self.can_switch_weapon = False
				self.weapon_switch_time = pygame.time.get_ticks()
				self.weapon_index = (self.weapon_index + 1) % len(weapon_data)
				self.weapon = list(weapon_data.keys())[self.weapon_index]

			if keys[pygame.K_e] and self.can_switch_magic:
				self.can_switch_magic = False
				self.magic_switch_time = pygame.time.get_ticks()
				self.magic_index = (self.magic_index + 1) % len(magic_data)
				self.magic = list(magic_data.keys())[self.magic_index]

	def get_status(self):
		if self.direction.x == 0 and self.direction.y == 0:
			if 'idle' not in self.status and 'attack' not in self.status:
				self.status += '_idle'

		if self.attacking:
			self.direction.xy = (0, 0)
			if 'attack' not in self.status:
				self.status = self.status.replace('_idle', '') + '_attack'
		else:
			self.status = self.status.replace('_attack', '')

	def cooldowns(self):
		current_time = pygame.time.get_ticks()

		if self.attacking:
			if current_time - self.attack_time >= self.attack_cooldown + weapon_data[self.weapon]['cooldown']:
				self.attacking = False
				self.destroy_attack()

		if not self.can_switch_weapon and current_time - self.weapon_switch_time >= self.switch_duration_cooldown:
			self.can_switch_weapon = True

		if not self.can_switch_magic and current_time - self.magic_switch_time >= self.switch_duration_cooldown:
			self.can_switch_magic = True

		if not self.vulnerable and current_time - self.hurt_time >= self.invulnerability_duration:
			self.vulnerable = True

	def animate(self):
		animation = self.animations[self.status]
		self.frame_index += self.animation_speed

		if self.frame_index >= len(animation):
			self.frame_index = 0

		self.image = animation[int(self.frame_index)]
		self.rect = self.image.get_rect(center=self.hitbox.center)
		self.image.set_alpha(self.wave_value() if not self.vulnerable else 255)

	def energy_recovery(self):
		if self.energy < self.stats['energy']:
			self.energy += 0.01 * self.stats['magic']
		else:
			self.energy = self.stats['energy']

	# ===== API REQUIRED BY Enemy =====
	def get_full_weapon_damage(self):
		return self.stats['attack'] + weapon_data[self.weapon]['damage']

	def get_full_magic_damage(self):
		return self.stats['magic'] + magic_data[self.magic]['strength']

	# ===== ABSTRACT METHODS =====
	def get_damage(self, amount, attack_type=None):
		if self.vulnerable:
			self.health -= amount
			self.vulnerable = False
			self.hurt_time = pygame.time.get_ticks()

	def update(self):
		self.input()
		self.cooldowns()
		self.get_status()
		self.animate()
		self.move(self.stats['speed'])
		self.energy_recovery()
