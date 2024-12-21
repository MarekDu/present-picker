import yaml
import random
from collections import defaultdict

def read_yaml(file_path):
    """Wczytuje dane z pliku YAML."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def write_yaml(data, file_path):
    """Zapisuje dane do pliku YAML."""
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True, sort_keys=False)

def redistribute_links(data, max_price=600):
    """Redistribuuje linki między osobami zgodnie z regułami."""
    all_links = []  # Wszystkie linki i ceny
    assigned = defaultdict(list)  # Nowe przypisania
    excluded = set()  # Osoby, które mają "dziecko: imię"

    # Zbieranie danych i identyfikacja wyjątków
    for entry in data:
        name = entry.get('Imię')
        link = entry.get('Link')
        price = entry.get('Cena')
        if isinstance(price, str) and 'zł' in price:
            price = int(price.replace('zł', '').strip())
        entry['Cena'] = price  # Upewniamy się, że cena to liczba

        # Jeśli to dziecko, dodaj do wyjątków
        if 'dziecko:' in name.lower():
            excluded.add(name)
            all_links.append({'name': name, 'link': link, 'price': price, 'is_child': True})
        else:
            all_links.append({'name': name, 'link': link, 'price': price, 'is_child': False})

    # Rozdzielanie linków
    random.shuffle(all_links)  # Losowa kolejność linków
    while all_links:
        for item in list(all_links):  # Iterujemy po kopii listy
            if item['price'] > max_price:
                distribute_large_link(item, assigned, max_price)
                all_links.remove(item)
            elif item['is_child']:
                reassign_child_link(item, assigned)
                all_links.remove(item)
            else:
                assign_standard_link(item, assigned, max_price)
                all_links.remove(item)

    # Przygotowanie wyników
    result = []
    for name, links in assigned.items():
        shared_links = find_shared_links(name, links, assigned)
        total_price = sum(link['price'] for link in links)
        result.append({
            'Imię': name,
            'Linki': [{'Link': link['link'], 'Cena': f"{link['price']} zł"} for link in links],
            'Współdzielone': [{'Link': link['link'], 'Cena': f"{link['price']} zł", 'Współdzielone z': shared_links[link['link']]} for link in links if link['link'] in shared_links],
            'Suma końcowa': f"{total_price} zł"
        })

    return result

def assign_standard_link(item, assigned, max_price):
    """Przypisuje standardowe linki, które mieszczą się w limicie."""
    for name, links in assigned.items():
        total_price = sum(link['price'] for link in links)
        if total_price + item['price'] <= max_price:
            assigned[name].append(item)
            return

def distribute_large_link(item, assigned, max_price):
    """Rozdziela link o wartości przekraczającej limit."""
    # Znajdź osoby o najmniejszej sumie cen
    totals = {name: sum(link['price'] for link in links) for name, links in assigned.items()}
    sorted_names = sorted(totals, key=totals.get)

    # Rozdziel cenę między osoby
    remaining_price = item['price']
    for name in sorted_names:
        if remaining_price <= 0:
            break
        total_price = sum(link['price'] for link in assigned[name])
        available_space = max_price - total_price
        if available_space > 0:
            portion = min(available_space, remaining_price)
            assigned[name].append({'link': item['link'], 'price': portion})
            remaining_price -= portion

def reassign_child_link(item, assigned):
    """Przypisuje link od dziecka do innej osoby."""
    # Znajdź osobę o najmniejszej sumie cen
    totals = {name: sum(link['price'] for link in links) for name, links in assigned.items()}
    target_name = min(totals, key=totals.get)
    assigned[target_name].append(item)

def find_shared_links(name, links, assigned):
    """Znajduje współdzielone linki."""
    shared = defaultdict(list)
    for link in links:
        for other_name, other_links in assigned.items():
            if other_name != name and any(other_link['link'] == link['link'] for other_link in other_links):
                shared[link['link']].append(other_name)
    return shared

if __name__ == "__main__":
    input_file = "dane/lista_prezentow.yaml"  # Plik wejściowy
    output_file = "dane/rozpiska_prezentow.yaml"  # Plik wyjściowy

    # Wczytaj dane
    try:
        data = read_yaml(input_file)
    except Exception as e:
        print(f"Błąd przy wczytywaniu pliku YAML: {e}")
        exit(1)

    # Przetwórz dane
    try:
        result = redistribute_links(data)
    except Exception as e:
        print(f"Błąd przy przetwarzaniu danych: {e}")
        exit(1)

    # Zapisz wynik
    try:
        write_yaml(result, output_file)
        print(f"Dane zostały zapisane do pliku: {output_file}")
    except Exception as e:
        print(f"Błąd przy zapisywaniu pliku YAML: {e}")
