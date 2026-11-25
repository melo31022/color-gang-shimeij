# Color Gang Shimeji (Python)

Uma adaptação em Python de um aplicativo de mascotes de desktop inspirado no funcionamento do projeto [Alan Becker's Stickfigures Unofficial](https://github.com/Skittlq/alan-beckers-stickfigures-unofficial), usando os sprites Color Gang que já pertencem a este repositório.

> Projeto não oficial e sem afiliação ou endosso de Alan Becker.

## Recursos

- Personagens em janelas transparentes e sempre no topo da área de trabalho.
- Movimento horizontal aleatório, pausas e pequenos pulos.
- Arraste os personagens com o botão esquerdo do mouse.
- Clique com o botão direito em um personagem para abrir o menu.
- Adicione várias cópias dos personagens ou remova um deles.
- Pausar, retomar, trazer os personagens para frente ou encerrar o aplicativo.
- Configuração simples por JSON.
- Implementação leve com Python e Tkinter, sem dependências externas.

## Requisitos

- Windows 10 ou Windows 11.
- Python 3.10 ou superior.
- Tkinter incluído na instalação do Python.

## Executar

1. Baixe ou clone este repositório.
2. Execute `run.bat`; ou abra um terminal nesta pasta e rode:

   ```powershell
   py -3 main.py
   ```

Não é necessário instalar pacotes com pip.

## Controles

- **Arrastar com o botão esquerdo:** mover o personagem.
- **Botão direito:** abrir o menu de opções.
- **Adicionar personagem:** criar outra cópia de Blue, Green, Red, The Second Coming ou Yellow.
- **Pausar todos / Retomar todos:** controlar o movimento de todos os mascotes.
- **Remover:** fechar apenas o personagem selecionado.
- **Sair:** encerrar o aplicativo.

## Configuração

Edite `settings.json` para alterar:

| Opção | Descrição |
| --- | --- |
| `start_all_characters` | Iniciar com todos os cinco personagens. |
| `max_characters` | Número máximo de janelas de personagens. |
| `speed` | Velocidade horizontal. |
| `tick_ms` | Intervalo de atualização em milissegundos. |
| `gravity` | Gravidade dos pulos. |
| `jump_strength` | Impulso vertical dos pulos. |
| `jump_probability` | Chance de pulo em cada atualização. |

Os personagens e seus arquivos de imagem são definidos em `characters.json`. Os caminhos dos sprites são relativos à pasta principal do repositório.

## Estado desta adaptação

O repositório Color Gang contém atualmente um sprite PNG estático por personagem. Por isso, esta primeira implementação movimenta os sprites existentes pela tela e simula pulos, mas ainda não possui ciclos completos de caminhada, dança, escalada ou interações animadas. Esses movimentos dependem de sequências adicionais de frames.

Esta é uma implementação Python independente, não uma tradução linha por linha do aplicativo Java original. Os arquivos Java compilados e os sprites de terceiros do projeto de referência não foram copiados para este repositório.

## Testes

Execute a partir da pasta principal:

```powershell
py -3 -m unittest discover -s tests -v
```

## Créditos e referências

- Projeto de referência: [Skittlq/alan-beckers-stickfigures-unofficial](https://github.com/Skittlq/alan-beckers-stickfigures-unofficial).
- Base conceitual Shimeji-ee: [Kilkakon's Shimeji](https://kilkakon.com/shimeji/).
- Os sprites usados por este aplicativo são os cinco arquivos PNG já presentes neste repositório.
