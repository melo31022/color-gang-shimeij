# Color Gang Shimeji — Python

Implementação Python de mascotes de desktop baseada no formato de animações do Shimeji-ee, utilizando os **assets originais** do projeto Skittlq/alan-beckers-stickfigures-unofficial.

> Projeto não oficial, sem afiliação ou endosso de Alan Becker, Skittlq ou Stickwave.

## Assets utilizados

O aplicativo NÃO utiliza os PNGs estáticos que já existiam na raiz deste repositório. Na primeira execução, ele baixa o arquivo-fonte do repositório original em um commit fixo e extrai somente:

- Os sprites PNG dos nove personagens.
- actions.xml e behaviors.xml de cada personagem.

Os personagens são Blue, Green, Orange, Purple, Red, The Second Coming, The Dark Lord, Yellow e Victim.

Os assets são armazenados localmente em assets/img/. O projeto original não é clonado como dependência: arquivos Java, JARs, instaladores, classes compiladas e arquivos não relacionados não são extraídos. A versão utilizada está fixada em 6e32aeb3956912c1d7d8396d885cb2b61be63193, evitando mudanças inesperadas no conteúdo baixado.

## Recursos

- Animações reais construídas a partir das sequências de Pose do actions.xml.
- Caminhada, corrida, dança, descanso, sentar, deitar e outras animações quando disponíveis para o personagem.
- Espelhamento dos sprites para mudar a direção do movimento.
- Personagens em janelas transparentes e sempre no topo da área de trabalho.
- Arrastar personagens com o botão esquerdo do mouse.
- Menu do botão direito para escolher animações, adicionar personagens, pausar ou remover mascotes.
- Cache limitado de quadros para reduzir o uso de memória.
- Configurações em JSON.

## Requisitos

- Windows 10 ou Windows 11.
- Python 3.10 ou superior.
- Conexão com a internet na primeira execução.
- Pillow (instalado automaticamente pelo run.bat).

## Executar

1. Baixe ou clone a branch python-port.
2. Extraia os arquivos.
3. Execute run.bat.

Alternativamente, pelo terminal:

    py -3 -m pip install -r requirements.txt
    py -3 main.py

Na primeira execução, o programa baixa e prepara os assets. Nas próximas execuções, utiliza o cache local e não precisa baixar tudo novamente.

## Controles

- Arrastar com o botão esquerdo: mover o personagem.
- Botão direito: abrir o menu.
- Adicionar personagem: criar outro mascote.
- Animação: escolher uma animação suportada pelo personagem selecionado.
- Pausar todos / Retomar todos: controlar todos os mascotes.
- Remover: fechar o mascote selecionado.
- Sair: encerrar o aplicativo.

## Configuração

Edite settings.json:

| Opção | Descrição |
| --- | --- |
| start_all_characters | Iniciar com todos os nove personagens. |
| max_characters | Máximo de mascotes simultâneos. |
| speed | Multiplicador de velocidade. |
| tick_ms | Intervalo de atualização em milissegundos. |
| random_action_min_seconds | Menor intervalo entre decisões de comportamento. |
| random_action_max_seconds | Maior intervalo entre decisões de comportamento. |
| dance_probability | Chance de incluir dança nas escolhas aleatórias. |
| sit_probability | Chance de incluir sentar nas escolhas aleatórias. |

## Créditos e licença

- Aplicativo de referência e assets: Skittlq/alan-beckers-stickfigures-unofficial.
- O README original credita Stickwave / @StickLaserPhase pelas animações, comportamentos, ações e sprites.
- A licença MIT do repositório original está incluída em UPSTREAM_LICENSE.txt.
- Esta adaptação Python é independente do runtime Java do Shimeji-ee.

Veja THIRD_PARTY_NOTICES.md para os avisos de terceiros.
