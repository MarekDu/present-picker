import yaml
import random
import os
from collections import defaultdict

def read_yaml(input_file):
    """Wczytuje dane z pliku YAML."""
    with open(input_file, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def write_txt_files(data, output_folder="output"):
    """Zapisuje dane końcowe do plików .txt, gdzie nazwy plików to wartości 'Imię'."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for person in data:
        name = person['Imię']
        filename = os.path.join(output_folder, f"{name}.txt")
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(f"Imię: {name}\n")
            file.write("Linki:\n")
            for link in person['Linki']:
                file.write(f"  - Link: {link['Link']}, Cena: {link['Cena']}\n")
            file.write("Współdzielone linki:\n")
            for shared in person['Współdzielone']:
                file.write(f"  - Link: {shared['Link']}, Cena: {shared['Cena']}, Współdzielone z: {', '.join(shared['Współdzielone z'])}\n")
            file.write(f"Suma końcowa: {person['Suma końcowa']}\n")

def assign_standard_link(item, assigned, max_price):
    """Przypisuje standardowe linki, które mieszczą się w limicie, uwzględniając równomierność."""
    best_candidate = None
    best_score = float('inf')

    for name, links in assigned.items():
        total_price = sum(link['price'] for link in links)
        num_links = len(links)
        score = total_price + num_links * 10  # Kombinacja sumy cen i liczby linków
        if total_price + item['price'] <= max_price and score < best_score:
            best_score = score
            best_candidate = name

    if best_candidate is not None:
        assigned[best_candidate].append(item)
    else:
        assigned[item['name']].append(item)

def distribute_large_link(item, assigned, max_price):
    """Rozdziela link o wartości przekraczającej limit, uwzględniając równomierność."""
    totals = {
        name: (sum(link['price'] for link in links), len(links)) for name, links in assigned.items()
    }
    sorted_names = sorted(totals, key=lambda x: (totals[x][0], totals[x][1]))

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
    """Przypisuje link od osoby z prefixem 'dziecko:' do innej osoby."""
    available_names = [name for name in assigned if name != item['name']]
    random.shuffle(available_names)
    assigned[available_names[0]].append(item)

def find_shared_links(name, links, assigned):
    """Znajduje współdzielone linki między osobami."""
    shared_links = defaultdict(list)
    for link in links:
        link_name = link['link']
        for other_name, other_links in assigned.items():
            if other_name != name:
                for other_link in other_links:
                    if other_link['link'] == link_name:
                        shared_links[link_name].append(other_name)
    return shared_links

def redistribute_links(data, max_price=600):
    """Redistribuuje linki między osobami, zapewniając równomierne przypisanie dla każdej osoby."""
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
        elif isinstance(price, int):
            pass
        else:
            continue  # Ignoruj niepoprawne ceny

        # Dodaj linki do listy
        if 'dziecko:' in name.lower():
            excluded.add(name)
            all_links.append({'name': name, 'link': link, 'price': price, 'is_child': True})
        else:
            all_links.append({'name': name, 'link': link, 'price': price, 'is_child': False})

    # Upewnij się, że każda osoba w danych wejściowych jest uwzględniona, nawet jeśli nie ma linków
    for entry in data:
        name = entry.get('Imię')
        if name not in excluded and name not in assigned:
            assigned[name] = []

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


if __name__ == "__main__":
    input_file = "data/lista_prezentow.yaml"  # Plik wejściowy
    output_folder = "output"  # Folder wyjściowy na pliki .txt

    # Wczytaj dane
    try:
        data = read_yaml(input_file)
        if not data:
            raise ValueError("Plik YAML jest pusty lub źle sformatowany.")
    except Exception as e:
        print(f"Błąd przy wczytywaniu pliku YAML: {e}")
        exit(1)

    # Przetwórz dane
    try:
        result = redistribute_links(data)
        if not result:
            raise ValueError("Nie udało się przetworzyć danych - brak wyników.")
    except Exception as e:
        print(f"Błąd przy przetwarzaniu danych: {e}")
        exit(1)

    # Zapisz wynik do plików .txt
    try:
        write_txt_files(result, output_folder)
        print(f"Dane zostały zapisane do plików w folderze: {output_folder}")
    except Exception as e:
        print(f"Błąd przy zapisywaniu plików .txt: {e}")
