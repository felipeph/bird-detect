# Bird Detection Pipeline

Um pipeline em Python utilizando OpenCV para detectar pássaros em imagens por meio de subtração de fundo (Background Subtraction).

## Instalação

As dependências são gerenciadas nativamente pelo `pip`.

1. Instale as dependências executando:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Para rodar a detecção em suas imagens, utilize o script de inicialização `bird_detect.py` na raiz do projeto:

```bash
python bird_detect.py --help
```

### Exemplos práticos

- **Rodar com os diretórios padrão** (`test_images/` para entrada e `output/` para saídas):
  ```bash
  python bird_detect.py
  ```

- **Rodar abrindo o menu interativo de configurações** (para alterar algoritmos, limiares, etc.):
  ```bash
  python bird_detect.py --menu
  ```

- **Rodar especificando diretórios de entrada/saída customizados**:
  ```bash
  python bird_detect.py --input minhas_imagens/ --out-detected saida/brutas/ --out-annotated saida/anotadas/
  ```
