import pygame
import numpy
import random

# ===================== КОНСТАНТЫ И НАСТРОЙКИ =====================
WIDTH = 400                    # Ширина игрового окна
HEIGHT = 300                   # Высота игрового окна
BACKGROUND = (0, 0, 0)         # Цвет фона

# Настройки генерации платформ
BOX_GAP = 100             # Вертикальный промежуток между платформами
PLATFORM_WIDTH_RANGE = (50, 100) # Диапазон ширины платформ
MAX_BOXES = 10             # Максимальное число платформ на экране

# ===================== КЛАССЫ ИГРОВЫХ ОБЪЕКТОВ =====================
class Sprite(pygame.sprite.Sprite):
    """Базовый класс для всех игровых спрайтов"""
    def __init__(self, image, startx, starty):
        super().__init__()

        self.image = pygame.image.load(image)
        self.rect = self.image.get_rect()
        self.rect.center = [startx, starty]

    def update(self):
        """Метод для обновления состояния (пустой в базовом классе)"""
        pass

    def draw(self, screen):
        """Отрисовка спрайта на экране"""    
        screen.blit(self.image, self.rect)


class Player(Sprite):
    """Класс игрового персонажа с физикой и анимациями (унаследован от Sprite)"""
    def __init__(self, startx, starty):
        super().__init__("p1_front.png", startx, starty)
        # Настройки анимаций
        self.stand_image = self.image
        self.jump_image = pygame.image.load("p1_jump.png")
        self.walk_cycle = [pygame.image.load(f"p1_walk{i:0>2}.png") for i in range(1,12)]
        self.animation_index = 0
        self.facing_left = False

        # Физические параметры
        self.speed = 4
        self.jumpspeed = 20
        self.vsp = 0
        self.gravity = 1
        self.min_jumpspeed = 4
        self.prev_key = pygame.key.get_pressed()

    def walk_animation(self):
        """Анимация ходьбы с переключением кадров"""
        self.image = self.walk_cycle[self.animation_index]
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)
        # Циклическое переключение кадров анимации
        if self.animation_index < len(self.walk_cycle)-1:
            self.animation_index += 1
        else:
            self.animation_index = 0

    def jump_animation(self):
        """Анимация прыжка"""
        self.image = self.jump_image
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self, boxes):
        """Основной метод обновления состояния персонажа"""
        hsp = 0 # Горизонтальная скорость
        # Проверка нахождения на земле
        onground = self.check_collision(0, 1, boxes)
        # Обработка ввода с клавиатуры (о божечки кошечки)
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.facing_left = True
            self.walk_animation()
            hsp = -self.speed
        elif key[pygame.K_RIGHT]:
            self.facing_left = False
            self.walk_animation()
            hsp = self.speed
        else:
            self.image = self.stand_image

        # Обработка прыжка
        if key[pygame.K_UP] and onground:
            self.vsp = -self.jumpspeed

        # Регулируемая высота прыжка
        if self.prev_key[pygame.K_UP] and not key[pygame.K_UP]:
            if self.vsp < -self.min_jumpspeed:
                self.vsp = -self.min_jumpspeed

        self.prev_key = key

        # Применение гравитации
        if self.vsp < 10 and not onground:  # 9.8 rounded up
            self.jump_animation()
            self.vsp += self.gravity
        # Сброс вертикальной скорости при касании земли
        if onground and self.vsp > 0:
            self.vsp = 0


        #=====ADD BY ME=====
        # Ограничение движения по горизонтали
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH

        
        # Перемещение персонажа
        self.move(hsp, self.vsp, boxes)

    def move(self, x, y, boxes):
        """Метод для обработки движения с коллизиями"""
        dx = x
        dy = y

        # Горизонтальное движение
        if dx != 0:
            move_x = self.get_collision_size_x(dx, boxes)
            self.rect.x += move_x  # сдвигаем по оси X на минимальное значение, чтобы избежать коллизии

        # Вертикальное движение
        if dy != 0:
            move_y = self.get_collision_size_y(dy, boxes)
            self.rect.y += move_y  # сдвигаем по оси Y на минимальное значение, чтобы избежать коллизии

    def get_collision_size_x(self, dx, boxes):
        """Возвращает на сколько нужно сдвигать по оси X, чтобы избежать коллизии"""
        step_x = int(numpy.sign(dx))
        while self.check_collision(step_x, 0, boxes):
            dx -= step_x  # уменьшаем сдвиг по оси X, пока не будет найдено свободное место
            if abs(dx) <= 1:  # Если сдвиг по X становится слишком малым (столкновение не удаётся разрешить), выходим
                break
        return dx

    def get_collision_size_y(self, dy, boxes):
        """Возвращает на сколько нужно сдвигать по оси Y, чтобы избежать коллизии"""
        step_y = int(numpy.sign(dy))
        while self.check_collision(0, step_y, boxes):
            dy -= step_y  # уменьшаем сдвиг по оси Y, пока не будет найдено свободное место
            if abs(dy) <= 1:  # Если сдвиг по Y становится слишком малым (столкновение не удаётся разрешить), выходим
                break
        return dy

    def check_collision(self, x, y, grounds):
        """Проверка коллизий с другими объектами"""
        self.rect.move_ip([x, y])
        collide = pygame.sprite.spritecollideany(self, grounds)
        self.rect.move_ip([-x, -y])
        return collide


class Box(Sprite):
    """Класс платформы-коробки"""
    def __init__(self, startx, starty, width=70):
        super().__init__("boxAlt.png", startx, starty)
        # Масштабирование изображения под нужную ширину
        self.image = pygame.transform.scale(self.image, (width, self.image.get_height()))


#=====ADD BY ME=====
# ===================== ИГРОВАЯ ЛОГИКА =====================
def generate_boxes(existing_boxes, player):
    """Генерация новых платформ при необходимости"""
    # Удаление платформ за пределами экрана
    for box in existing_boxes:
        if box.rect.top > HEIGHT + 75:
            box.kill()

    # Генерация новых платформ
    while len(existing_boxes) < MAX_BOXES:
        #width = random.randint(*PLATFORM_WIDTH_RANGE) не меняю
        width = 70
        # Найдём самую нижнюю коробку, если она есть ОСТОРОДНО НАЙДЕНА ЛЯМБДА
        if existing_boxes:
            top_box = min(existing_boxes, key=lambda b: b.rect.top)
            y = top_box.rect.top - BOX_GAP
            #x = lowest_box.rect.left - BOX_GAP
        else:
            # Если нет платформ, начнём с нижней части экрана
            y = HEIGHT - 100  # Первая коробка
            #x = random.randint(0, WIDTH - width)
        
        x = random.randint(0, WIDTH - width)

        # Проверка, чтобы не создать коробку с перекрытием (опционально)
        too_close = abs(abs(player.rect.centerx - x) < width and abs(player.rect.centery - y) < BOX_GAP)
        if too_close:
            continue  # Попробуем снова
            
        too_close = any(
            abs(box.rect.centerx - x) < width and abs(box.rect.centery - y) < BOX_GAP
            for box in existing_boxes
        )
        if too_close:
            continue  # Попробуем снова
            
        # Добавление платформы
        new_box = Box(x, y) #Параметр width и так по умолчанию 70
        existing_boxes.add(new_box)
        
def main():
    """Основная функция игры"""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    # Создание игровых объектов
    player = Player(100, 200)

    boxes = pygame.sprite.Group()
    for bx in range(0, 500, 70):
        boxes.add(Box(bx, 300))

    #boxes.add(Box(330, 230))

    while True:
        pygame.event.pump() 
        # Обработка событий (добавлен выход)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return    
        
        player.update(boxes)
        generate_boxes(boxes, player)
        
        # Прокрутка платформ вниз при достижении верхней части экрана
        if player.rect.top < HEIGHT // 4:
            player.rect.top = HEIGHT // 4
            for box in boxes:
                box.rect.y += abs(player.vsp)
                
        # Отрисовка
        screen.fill(BACKGROUND)
        player.draw(screen)
        boxes.draw(screen)
        pygame.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    main()