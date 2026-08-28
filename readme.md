# 🎵 YouTube Music Sync

Aplicativo desktop em Python para sincronizar automaticamente uma playlist do YouTube com uma biblioteca local de músicas.

O programa verifica quais músicas da playlist já estão na biblioteca e baixa apenas as que ainda não foram encontradas.

## ✨ Recursos

* 🎵 Sincronização automática de playlists
* 🔎 Verificação de músicas já existentes
* 💾 Registro das músicas em `library.json`
* ⬇️ Download somente de músicas novas
* 🎧 Conversão automática para MP3
* 🔐 Suporte a cookies do navegador para playlists privadas
* 🦊 Suporte a Firefox
* 📊 Barra de progresso e estatísticas
* 📝 Log detalhado durante a sincronização
* 🖥️ Interface gráfica com Tkinter
* 📁 Biblioteca local configurável

## 🛠️ Tecnologias

* Python
* Tkinter
* yt-dlp
* Node.js
* FFmpeg

## 📋 Requisitos

Antes de executar o programa, instale:

* **Python 3.11 ou superior**
* **yt-dlp**
* **Node.js**
* **FFmpeg**
* Um navegador compatível com `--cookies-from-browser`

O navegador configurado por padrão é o **Firefox**.

## 📦 Instalação

Clone o repositório:

```bash
git clone https://github.com/SEU_USUARIO/youtube-music-sync.git
cd youtube-music-sync
```

Instale as dependências Python:

```bash
py -m pip install -r requirements.txt
```

Verifique se o yt-dlp está instalado:

```bash
yt-dlp --version
```

Também verifique o Node.js:

```bash
node --version
```

E o FFmpeg:

```bash
ffmpeg -version
```

## ▶️ Executando

Execute:

```bash
py main.py
```

A interface gráfica será aberta.

Informe a URL da playlist, escolha a pasta da biblioteca e clique em:

**🔄 Sincronizar**

O programa irá:

1. Ler a playlist.
2. Verificar as músicas existentes.
3. Comparar os IDs e os nomes das músicas.
4. Identificar quais músicas são novas.
5. Baixar somente as músicas novas.
6. Converter os downloads para MP3.
7. Registrar as músicas no `library.json`.

## 🔐 Playlists privadas

O programa utiliza:

```text
--cookies-from-browser firefox
```

Isso permite que o yt-dlp utilize a sessão autenticada do navegador para acessar conteúdos que sua conta consegue visualizar.

Você precisa estar conectado à conta correta no Firefox.

**Nunca compartilhe arquivos de cookies, credenciais ou dados de sessão.**

## ⚙️ Configuração do yt-dlp

O programa utiliza alguns parâmetros específicos para o YouTube:

```text
--js-runtimes node
--remote-components ejs:github
--cookies-from-browser firefox
--extractor-args youtube:player_client=android_vr,web_embedded
--no-playlist
```

Essas opções são usadas para melhorar a compatibilidade com o YouTube e evitar que URLs individuais sejam tratadas como playlists.

## 📁 Estrutura do projeto

```text
youtube-music-sync/
│
├── main.py
├── requirements.txt
├── .gitignore
├── README.md
└── library.json
```

> `library.json` é gerado automaticamente e deve permanecer apenas localmente.

## 💾 Biblioteca

O programa mantém um arquivo:

```text
library.json
```

Esse arquivo registra informações sobre as músicas já processadas, incluindo:

* ID do vídeo
* título
* URL
* origem do arquivo
* caminho local, quando disponível

Isso permite que futuras sincronizações sejam mais rápidas e evitem downloads duplicados.

## 🎧 Formato dos arquivos

As músicas são salvas no formato:

```text
Nome da Música [VIDEO_ID].mp3
```

Por exemplo:

```text
2 Phut Hon Funk 2.0 (Super Slowed + Reverb) [XBMu5c5rN8E].mp3
```

## 🔒 Segurança

Este projeto utiliza cookies do navegador apenas para autenticação no YouTube.

Não envie para o GitHub:

* cookies do navegador
* arquivos de autenticação
* `library.json`, caso não queira compartilhá-lo
* qualquer arquivo contendo dados pessoais

O `.gitignore` já deve impedir que arquivos locais sensíveis sejam adicionados acidentalmente.

## ⚠️ Observações

O projeto utiliza o **yt-dlp** para acessar e baixar conteúdo disponibilizado pelo YouTube.

Use o programa somente para conteúdos que você tem permissão para baixar e de acordo com os termos aplicáveis ao serviço e à sua região.

O funcionamento pode mudar caso o YouTube altere seus sistemas de entrega ou autenticação. A internet, essa máquina de estados mal documentada, não promete estabilidade eterna.

## 📄 Licença

Este projeto está disponível sob a licença **MIT**.

Consulte o arquivo `LICENSE` para mais informações.
