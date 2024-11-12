# TODO
# safe area on new life
# sounds thump

# Notes:
# random.randrange returns an int
# random.uniform returns a float
# p for pause
# j for toggle showing FPS
# o for frame advance whilst paused

import pygame
import sys
import os
import random
from pygame.locals import *
from util.vectorsprites import *
from ship import *
from stage import *
from badies import *
from shooter import *
from soundManager import *


class Asteroids():

    explodingTtl = 180

    def __init__(self):
        self.stage = Stage('Atari Asteroids', (800, 600))
        self.paused = False
        self.showingFPS = False
        self.frameAdvance = False
        self.gameState = "attract_mode"
        self.rockList = []
        self.saucer = None
        self.secondsCount = 1
        self.score = 0
        self.ship = None
        self.lives = 0
        self.selected_difficulty = 0
        self.difficulty = "Fácil"  # Valor predeterminado para la dificultad
        self.background_image = pygame.image.load('../res/space_background.jpg')
        screen_width = 800
        screen_height = 450
        self.background_image = pygame.transform.scale(self.background_image, (screen_width, screen_height))
        self.rock_speed = 1.0  # Velocidad predeterminada para los asteroides
        self.ship_speed = 1.0  # Velocidad predeterminada para la nave



    def initialiseGame(self):
        self.gameState = 'playing'
        [self.stage.removeSprite(sprite) for sprite in self.rockList]
        if self.saucer is not None:
            self.killSaucer()

        self.startLives = 5
        self.createNewShip()
        self.createLivesList()
        self.score = 0
        self.rockList = []

        # Configuración según la dificultad
        if self.difficulty == "Fácil":
            self.numRocks = 3
            self.rock_speed = 1
            self.ship_speed = 1
        elif self.difficulty == "Medio":
            self.numRocks = 5
            self.rock_speed = 1.5
            self.ship_speed = 1.2
        elif self.difficulty == "Difícil":
            self.numRocks = 7
            self.rock_speed = 2
            self.ship_speed = 1.5

        self.nextLife = 10000
        self.createRocks(self.numRocks)
        self.secondsCount = 1


    def createNewShip(self):
        if self.ship:
            [self.stage.spriteList.remove(debris) for debris in self.ship.shipDebrisList]
        self.ship = Ship(self.stage)
        self.ship.speed = self.ship_speed  
        self.stage.addSprite(self.ship.thrustJet)
        self.stage.addSprite(self.ship)


    def createLivesList(self):
        self.lives += 1
        self.livesList = []
        for i in range(1, self.startLives):
            self.addLife(i)

    def addLife(self, lifeNumber):
        self.lives += 1
        ship = Ship(self.stage)
        self.stage.addSprite(ship)
        ship.position.x = self.stage.width - \
            (lifeNumber * ship.boundingRect.width) - 10
        ship.position.y = 0 + ship.boundingRect.height
        self.livesList.append(ship)

    def createRocks(self, numRocks):
        for _ in range(0, numRocks):
            position = Vector2d(random.randrange(-10, 10), random.randrange(-10, 10))
            newRock = Rock(self.stage, position, Rock.largeRockType)
            newRock.speed = self.rock_speed  
            self.stage.addSprite(newRock)
            self.rockList.append(newRock)


    def playGame(self):

        clock = pygame.time.Clock()

        frameCount = 0.0
        timePassed = 0.0
        self.fps = 0.0
        # Main loop
        while True:

            # calculate fps
            timePassed += clock.tick(60)
            frameCount += 1
            if frameCount % 10 == 0:  # every 10 frames
                # nearest integer
                self.fps = round((frameCount / (timePassed / 1000.0)))
                # reset counter
                timePassed = 0
                frameCount = 0

            self.secondsCount += 1

            self.input(pygame.event.get())

            # pause
            if self.paused and not self.frameAdvance:
                self.displayPaused()
                continue

            self.stage.screen.fill((10, 10, 10))
            self.stage.moveSprites()
            self.stage.drawSprites()
            self.doSaucerLogic()
            self.displayScore()
            if self.showingFPS:
                self.displayFps()  # for debug
            self.checkScore()

            # Process keys
            if self.gameState == 'playing':
                self.playing()
            elif self.gameState == 'exploding':
                self.exploding()
            else:
                self.displayText()

            # Double buffer draw
            pygame.display.flip()

    def playing(self):
        if self.lives == 0:
            self.stopAllSounds()
            self.gameState = 'attract_mode'
        else:
            self.processKeys()
            self.checkCollisions()
            if len(self.rockList) == 0:
                self.levelUp()

    def doSaucerLogic(self):
        if self.saucer is not None:
            if self.saucer.laps >= 2:
                self.killSaucer()

        # Create a saucer
        if self.secondsCount % 2000 == 0 and self.saucer is None:
            randVal = random.randrange(0, 10)
            if randVal <= 3:
                self.saucer = Saucer(
                    self.stage, Saucer.smallSaucerType, self.ship)
            else:
                self.saucer = Saucer(
                    self.stage, Saucer.largeSaucerType, self.ship)
            self.stage.addSprite(self.saucer)

    def exploding(self):
        self.explodingCount += 1
        if self.explodingCount > self.explodingTtl:
            self.gameState = 'playing'
            [self.stage.spriteList.remove(debris)
             for debris in self.ship.shipDebrisList]
            self.ship.shipDebrisList = []

            if self.lives == 0:
                self.ship.visible = False
            else:
                self.createNewShip()

    def levelUp(self):
        self.numRocks += 1
        self.createRocks(self.numRocks)

    def displayText(self):
        # Escalar la imagen de fondo para que ocupe toda la pantalla
        self.background_image = pygame.transform.scale(self.background_image, (self.stage.width, self.stage.height))
        self.stage.screen.blit(self.background_image, (0, 0))

        # Configurar y mostrar el título en un tamaño más grande y en "negrita"
        font1 = pygame.font.Font('../res/Hyperspace.otf', 80)  # Tamaño grande para el título
        titleText = font1.render('Asteroids', True, (255, 255, 255))  # Color blanco brillante
        titleTextRect = titleText.get_rect(centerx=self.stage.width / 2, y=50)

        # Simular negrita para el título dibujándolo varias veces con desplazamiento
        for offset in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            self.stage.screen.blit(titleText, titleTextRect.move(offset))
        self.stage.screen.blit(titleText, titleTextRect)

        # Configurar y mostrar los botones de dificultad en un tamaño más grande y en "negrita"
        font3 = pygame.font.Font('../res/Hyperspace.otf', 50)  # Tamaño grande para los botones

        # Renderizar y simular negrita para cada botón de dificultad
        easy_text = font3.render('Fácil', True, (255, 255, 255) if self.selected_difficulty == 0 else (200, 200, 200))
        medium_text = font3.render('Medio', True, (255, 255, 255) if self.selected_difficulty == 1 else (200, 200, 200))
        hard_text = font3.render('Difícil', True, (255, 255, 255) if self.selected_difficulty == 2 else (200, 200, 200))

        # Aumentar la separación horizontal entre los botones
        easy_rect = easy_text.get_rect(centerx=self.stage.width / 2 - 200, centery=self.stage.height - 80)
        medium_rect = medium_text.get_rect(centerx=self.stage.width / 2, centery=self.stage.height - 80)
        hard_rect = hard_text.get_rect(centerx=self.stage.width / 2 + 200, centery=self.stage.height - 80)

        # Dibujar los botones con simulación de negrita
        for offset in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            self.stage.screen.blit(easy_text, easy_rect.move(offset))
            self.stage.screen.blit(medium_text, medium_rect.move(offset))
            self.stage.screen.blit(hard_text, hard_rect.move(offset))

        # Dibujar el texto principal de cada botón para que quede encima y más definido
        self.stage.screen.blit(easy_text, easy_rect)
        self.stage.screen.blit(medium_text, medium_rect)
        self.stage.screen.blit(hard_text, hard_rect)

    def stopAllSounds(self):
        stopSound("thrust")
        stopSound("explode1")
        stopSound("explode2")
        stopSound("explode3")
        stopSound("fire")
        stopSound("lsaucer")
        stopSound("ssaucer")
        stopSound("extralife")


    def displayScore(self):
        font1 = pygame.font.Font('../res/Hyperspace.otf', 30)
        scoreStr = str("%02d" % self.score)
        scoreText = font1.render(scoreStr, True, (200, 200, 200))
        scoreTextRect = scoreText.get_rect(centerx=100, centery=45)
        self.stage.screen.blit(scoreText, scoreTextRect)

    def displayPaused(self):
        if self.paused:
            font1 = pygame.font.Font('../res/Hyperspace.otf', 30)
            pausedText = font1.render("Paused", True, (255, 255, 255))
            textRect = pausedText.get_rect(
                centerx=self.stage.width/2, centery=self.stage.height/2)
            self.stage.screen.blit(pausedText, textRect)
            pygame.display.update()

    def input(self, events):
        self.frameAdvance = False
        for event in events:
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    sys.exit(0)

                # Cambiar dificultad en el menú de inicio
                if self.gameState == 'attract_mode':
                    if event.key == K_LEFT:
                        self.selected_difficulty = (self.selected_difficulty - 1) % 3
                        playSound("fire")  # Reproduce sonido al moverse
                    elif event.key == K_RIGHT:
                        self.selected_difficulty = (self.selected_difficulty + 1) % 3
                        playSound("fire")  # Reproduce sonido al moverse
                    elif event.key == K_RETURN:
                        # Asignar el nivel de dificultad según el botón seleccionado
                        if self.selected_difficulty == 0:
                            self.difficulty = "Fácil"
                        elif self.selected_difficulty == 1:
                            self.difficulty = "Medio"
                        elif self.selected_difficulty == 2:
                            self.difficulty = "Difícil"
                        self.initialiseGame()  # Iniciar el juego

                # Controles en el estado de juego "playing"
                elif self.gameState == 'playing':
                    if event.key == K_SPACE:
                        if self.ship:  # Asegurarse de que la nave exista
                            self.ship.fireBullet()  # Disparar el arma de la nave
                    elif event.key == K_b:
                        if self.ship:
                            self.ship.fireBullet()
                    elif event.key == K_h:
                        if self.ship:
                            self.ship.enterHyperSpace()
                    elif event.key == K_m:
                        self.returnToMenu() 
                    
                # Otros controles generales
                if event.key == K_p:
                    self.paused = not self.paused


    def processKeys(self):
        key = pygame.key.get_pressed()

        if key[K_LEFT] or key[K_z]:
            self.ship.rotateLeft()
        elif key[K_RIGHT] or key[K_x]:
            self.ship.rotateRight()

        if key[K_UP] or key[K_n]:
            self.ship.increaseThrust()
            self.ship.thrustJet.accelerating = True
        else:
            self.ship.thrustJet.accelerating = False

    # Check for ship hitting the rocks etc.

    def checkCollisions(self):

        # Ship bullet hit rock?
        newRocks = []
        shipHit, saucerHit = False, False

        # Rocks
        for rock in self.rockList:
            rockHit = False

            if not self.ship.inHyperSpace and rock.collidesWith(self.ship):
                p = rock.checkPolygonCollision(self.ship)
                if p is not None:
                    shipHit = True
                    rockHit = True

            if self.saucer is not None:
                if rock.collidesWith(self.saucer):
                    saucerHit = True
                    rockHit = True

                if self.saucer.bulletCollision(rock):
                    rockHit = True

                if self.ship.bulletCollision(self.saucer):
                    saucerHit = True
                    self.score += self.saucer.scoreValue

            if self.ship.bulletCollision(rock):
                rockHit = True

            if rockHit:
                self.rockList.remove(rock)
                self.stage.spriteList.remove(rock)

                if rock.rockType == Rock.largeRockType:
                    playSound("explode1")
                    newRockType = Rock.mediumRockType
                    self.score += 50
                elif rock.rockType == Rock.mediumRockType:
                    playSound("explode2")
                    newRockType = Rock.smallRockType
                    self.score += 100
                else:
                    playSound("explode3")
                    self.score += 200

                if rock.rockType != Rock.smallRockType:
                    # new rocks
                    for _ in range(0, 2):
                        position = Vector2d(rock.position.x, rock.position.y)
                        newRock = Rock(self.stage, position, newRockType)
                        self.stage.addSprite(newRock)
                        self.rockList.append(newRock)

                self.createDebris(rock)

        # Saucer bullets
        if self.saucer is not None:
            if not self.ship.inHyperSpace:
                if self.saucer.bulletCollision(self.ship):
                    shipHit = True

                if self.saucer.collidesWith(self.ship):
                    shipHit = True
                    saucerHit = True

            if saucerHit:
                self.createDebris(self.saucer)
                self.killSaucer()

        if shipHit:
            self.killShip()

            # comment in to pause on collision
            #self.paused = True

    def killShip(self):
        stopSound("thrust")
        playSound("explode2")
        self.explodingCount = 0
        self.lives -= 1
        if (self.livesList):
            ship = self.livesList.pop()
            self.stage.removeSprite(ship)

        self.stage.removeSprite(self.ship)
        self.stage.removeSprite(self.ship.thrustJet)
        self.gameState = 'exploding'
        self.ship.explode()

    def killSaucer(self):
        stopSound("lsaucer")
        stopSound("ssaucer")
        playSound("explode2")
        self.stage.removeSprite(self.saucer)
        self.saucer = None

    def createDebris(self, sprite):
        for _ in range(0, 25):
            position = Vector2d(sprite.position.x, sprite.position.y)
            debris = Debris(position, self.stage)
            self.stage.addSprite(debris)

    def displayFps(self):
        font2 = pygame.font.Font('../res/Hyperspace.otf', 15)
        fpsStr = str(self.fps)+(' FPS')
        scoreText = font2.render(fpsStr, True, (255, 255, 255))
        scoreTextRect = scoreText.get_rect(
            centerx=(self.stage.width/2), centery=15)
        self.stage.screen.blit(scoreText, scoreTextRect)

    def checkScore(self):
        if self.score > 0 and self.score > self.nextLife:
            playSound("extralife")
            self.nextLife += 10000
            self.addLife(self.lives)
    
    def returnToMenu(self):
        self.stopAllSounds()
        self.gameState = "attract_mode"

        # Limpiar elementos de juego
        if self.ship:
            self.stage.removeSprite(self.ship)
            self.stage.removeSprite(self.ship.thrustJet)
            self.ship = None

        for rock in self.rockList:
            self.stage.removeSprite(rock)
        self.rockList.clear()

        if self.saucer:
            self.stage.removeSprite(self.saucer)
            self.saucer = None

        # Reiniciar el puntaje y otros contadores si es necesario
        self.score = 0
        self.lives = 0
        self.secondsCount = 1



# Script to run the game
if not pygame.font:
    print('Warning, fonts disabled')
if not pygame.mixer:
    print('Warning, sound disabled')

initSoundManager()
game = Asteroids()  # create object game from class Asteroids
game.playGame()

####
