import pandas as pd
import yaml

def excel_to_yaml(input_file, output_file):
    # Wczytanie danych z pliku Excel
    try:
        data = pd.read_excel(input_file)
    except Exception as e:
        print(f"Błąd przy wczytywaniu pliku: {e}")
        return

    # Sprawdzenie, czy wymagane kolumny istnieją
    required_columns = ['Imię', 'Link', 'Cena']
    if not all(col in data.columns for col in required_columns):
        print(f"Plik Excel musi zawierać kolumny: {', '.join(required_columns)}")
        return

    # Sortowanie danych po kolumnie "Imię"
    data_sorted = data.sort_values(by='Imię')

    # Konwersja danych do listy słowników
    data_list = data_sorted.to_dict(orient='records')

    # Zapisanie do pliku YAML
    try:
        with open(output_file, 'w', encoding='utf-8') as yaml_file:
            yaml.dump(data_list, yaml_file, allow_unicode=True, sort_keys=False)
        print(f"Dane zostały zapisane do pliku: {output_file}")
    except Exception as e:
        print(f"Błąd przy zapisywaniu pliku YAML: {e}")

# Użycie funkcji
if __name__ == "__main__":
    input_file = "data/lista_prezentow.xlsx"
    output_file = "data/lista_prezentow.yaml"
    excel_to_yaml(input_file, output_file)
