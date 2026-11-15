# Como testar o app no celular Android

Há dois caminhos. O **Caminho A** é o mais fácil e não exige instalar o Android Studio.

## Caminho A: baixar o APK gerado pelo GitHub (sem Android Studio)

Todo `git push` roda o workflow **CI**, que compila o app e gera um APK.

1. No GitHub, abra a aba **Actions** do repositório e clique na execução mais recente do **CI**.
2. No final da página, em **Artifacts**, baixe `iara-campo-debug-apk` (vem em .zip).
3. Envie o `app-debug.apk` para o celular (Google Drive, e-mail ou cabo USB).
4. No celular, toque no arquivo. O Android vai pedir para **permitir instalar apps desta fonte**:
   aceite. É normal, porque o app não vem da Play Store.
5. Abra o **Iara Campo**.

## Caminho B: pelo Android Studio (para editar o código)

1. Instale o [Android Studio](https://developer.android.com/studio).
2. **File → Open** e escolha a pasta `android-field-copilot`. Espere o Gradle sincronizar
   (na primeira vez, demora alguns minutos).
3. No celular, ative o **modo desenvolvedor**: *Configurações → Sobre o telefone* → toque
   7 vezes em **Número da versão**. Depois, em *Opções do desenvolvedor*, ative a
   **Depuração USB**.
4. Ligue o celular no computador pelo cabo, aceite a autorização que aparece na tela e
   clique em **Run ▶** no Android Studio.

## Testando o fluxo completo (celular + servidor)

### 1. Suba o servidor no computador
```bash
docker compose up --build
```

### 2. Descubra o IP do computador na rede Wi-Fi
- Windows: `ipconfig` → "Endereço IPv4" (ex.: `192.168.0.15`)
- Mac/Linux: `ip addr` ou `ifconfig` → endereço que começa com `192.168.` ou `10.`

O celular e o computador precisam estar **na mesma rede Wi-Fi**.

### 3. Configure o app
Aba **Ajustes** → Endereço do servidor: `http://192.168.0.15:8000` (com o seu IP) → **Salvar**.

### 4. Colete um relato SEM internet
1. Ative o **modo avião** no celular (o GPS continua funcionando).
2. Aba **Campo**: digite ou fale (🎤) algo como:
   *"Dona Raimunda tira o óleo da semente da andiroba"*.
3. Responda às perguntas do agente (indicação, preparo, época, comunidade, consentimento).
4. Toque em **📷 Foto**. O app avalia na hora se a foto está nítida e bem iluminada.
5. Toque em **📍 GPS** e aceite a permissão (perto de uma janela ou ao ar livre funciona melhor).
6. Toque em **💾 Salvar**. Na aba **Registros**, o relato aparece como "⏳ Na fila".

### 5. Volte a ter internet
Desligue o modo avião. Em alguns segundos o registro muda para "✔ Enviado ao servidor"
(ou toque em **🔄 Sincronizar agora**). Abra o painel em `http://localhost:8080`: o registro
aparece no mapa com o parecer dos três agentes.

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| Fica sempre "Na fila" | IP errado nos Ajustes, celular em outra rede ou firewall do computador bloqueando a porta 8000 |
| 🎤 não faz nada | O celular não tem reconhecimento de voz instalado. Para funcionar offline, baixe o pacote de português em *Configurações → Google → Voz → Reconhecimento offline* |
| GPS demora | Na primeira vez sem internet o GPS pode levar alguns minutos para achar satélites. Vá para um lugar aberto |
| "Não reconheci o nome" | A planta não está no dicionário embarcado (10 espécies no MVP). Responda só com o nome, que ele aceita |
