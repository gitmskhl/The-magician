import random

# Размер сетки (ширина и высота)
width, height = 50, 50
grid = [[1 for _ in range(width)] for _ in range(height)]  # 1 = стена, 0 = проход, 2 = ловушка

def generate_tunnels(x, y, direction=None):
    grid[y][x] = 0  # Проход
    
    # Направления с приоритетом вниз
    directions = [(0, 2, "down"), (2, 0, "right"), (-2, 0, "left"), (0, -2, "up")]
    weights = [0.7, 0.15, 0.15, 0.0]  # Шанс: вниз 70%, влево/вправо 15%, вверх 0%
    random_dir = random.choices(directions, weights=weights, k=1)[0]
    directions.remove(random_dir)  # Убираем выбранное направление
    directions.insert(0, random_dir)  # Ставим его первым для приоритета
    
    for dx, dy, dir_name in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == 1:
            # Прокапываем путь
            grid[y + dy // 2][x + dx // 2] = 0
            generate_tunnels(nx, ny, dir_name)
    
    # Добавляем ловушки в случайных местах
    if random.random() < 0.1 and direction != "up":  # 10% шанс на ловушку
        grid[y][x] = 2

# Старт сверху
generate_tunnels(width // 2, 0)

# Вывод карты
for row in grid:
    print(" ".join("#" if cell == 1 else "." if cell == 0 else "T" for cell in row))