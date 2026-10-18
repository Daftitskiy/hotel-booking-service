CREATE TABLE IF NOT EXISTS hotels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    stars INT NOT NULL,
    price_standard NUMERIC(12, 2) NOT NULL,
    price_deluxe NUMERIC(12, 2) NOT NULL,
    price_suite NUMERIC(12, 2) NOT NULL,
    description TEXT,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    hotel_id INT REFERENCES hotels(id) ON DELETE SET NULL,
    hotel_name VARCHAR(150) NOT NULL,
    guest_name VARCHAR(100) NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    total_price NUMERIC(14, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO hotels (name, city, stars, price_standard, price_deluxe, price_suite, description, image_url)
VALUES 
    (
        'Гранд Отель Европа',
        'Санкт-Петербург',
        5,
        5500.00,
        9500.00,
        17000.00,
        'Исторический пятизвездочный отель в самом сердце Санкт-Петербурга с роскошными интерьерами.',
        'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=600&q=80'
    ),
    (
        'Метрополь Престиж',
        'Москва',
        5,
        6200.00,
        11000.00,
        21000.00,
        'Легендарный отель рядом с Красной площадью, сочетающий традиции и сервис мирового уровня.',
        'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=600&q=80'
    ),
    (
        'Морской Бриз Спа & Резорт',
        'Сочи',
        4,
        3800.00,
        6500.00,
        12500.00,
        'Курортный комплекс на первой береговой линии с собственным спа-центром и открытыми бассейнами.',
        'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=600&q=80'
    ),
    (
        'Алтай Эко Вилладж',
        'Горно-Алтайск',
        4,
        4200.00,
        7000.00,
        13000.00,
        'Уютные эко-коттеджи в окружении горных вершин и реликтового хвойного леса.',
        'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=600&q=80'
    );

INSERT INTO bookings (hotel_id, hotel_name, guest_name, room_type, check_in, check_out, total_price)
VALUES 
    (1, 'Гранд Отель Европа', 'Иванов Иван Иванович', 'standard', '2026-06-01', '2026-06-05', 22000.00),
    (3, 'Морской Бриз Спа & Резорт', 'Смирнова Анна Сергеевна', 'deluxe', '2026-07-10', '2026-07-15', 32500.00);
