# Conectarse a la GPU desde VS Code

[Seguro] Acceso SSH por clave comprobado el 23/10/2026 y conexión desde VS Code confirmada por el usuario ese día. Estos pasos quedan como referencia para volver a conectarse. Los adjuntos están en `.gpu-private`, con permisos restringidos y excluidos de Git.

1. Abrí VS Code en tu computadora.
2. **Remote - SSH** de **Microsoft** (`ms-vscode-remote.remote-ssh`) ya figura instalada en esta computadora. En otra computadora se instala desde Extensiones (**Ctrl+Shift+X**).
3. Abrí la paleta con **Ctrl+Shift+P** y ejecutá **Remote-SSH: Open SSH Configuration File...**.
4. Elegí `C:\Users\dagus\.ssh\config`.
5. Agregá al final este bloque completo, conservando las entradas existentes, y guardá:

```sshconfig
Host investigathon-gpu
    HostName 18.227.123.98
    User ubuntu
    IdentityFile C:/Users/dagus/Desktop/laburos/Competencias/investigathon/.gpu-private/investigathon-gpu.key
    UserKnownHostsFile C:/Users/dagus/Desktop/laburos/Competencias/investigathon/.gpu-private/known_hosts
    StrictHostKeyChecking yes
    IdentitiesOnly yes
    ServerAliveInterval 30
```

6. Ejecutá **Remote-SSH: Connect to Host...** desde la paleta.
7. Seleccioná **investigathon-gpu**. Si pregunta el sistema operativo, elegí **Linux**.
8. Esperá la instalación automática de VS Code Server. Al conectar, la esquina inferior izquierda mostrará **SSH: investigathon-gpu**.
9. En esa ventana, elegí **File > Open Folder...** (Archivo > Abrir carpeta) e ingresá `/home/ubuntu/investigathon`.
10. Abrí **Terminal > New Terminal**. Para seguir la instalación en vivo, pegá:

```bash
tail -n 50 -f /home/ubuntu/investigathon/logs/bootstrap.log
```

11. En otra terminal, podés consultar estado y GPU:

```bash
cat /home/ubuntu/investigathon/setup-status.txt
nvidia-smi
```

[Seguro] `Ctrl+C` termina el seguimiento de `tail`; el instalador corre separado y continúa. Los scripts están en `gpu/`, los modelos en `models/` y las pruebas en `results/`. Cerrar VS Code o SSH no apaga la máquina.

[Seguro] Si dice `Permission denied (publickey)`, comprobá que `User` sea `ubuntu` y que `IdentityFile` apunte al archivo existente. Si pide contraseña, verificá que elegiste el alias correcto y revisá **View > Output > Remote - SSH**. Si aparece un error de identidad del host, conservá la comprobación estricta: la huella del mail es `SHA256:I721clfKbN+y/pYKhnVGYJvKaRJphs6J4WwO6vLO+Qk`; una identidad distinta requiere resolver la discrepancia antes de conectar.

Fuente: [documentación oficial de VS Code Remote - SSH](https://code.visualstudio.com/docs/remote/ssh).

## Claude Code en la máquina remota

[Seguro] Se instaló Claude Code **2.1.308**, canal estable, para `ubuntu` con el instalador oficial. El ejecutable está en `/home/ubuntu/.local/bin/claude`; se agregó ese directorio a `~/.bashrc` y se verificaron `claude --version` y `claude --help` en una sesión nueva. No se inició sesión en tu cuenta ni se enviaron prompts a Claude.

1. En la terminal remota que ya estaba abierta, ejecutá `source ~/.bashrc` una vez. En terminales nuevas ya se carga el PATH.
2. Ejecutá `cd /home/ubuntu/investigathon`.
3. Ejecutá `claude`.
4. Si pide autenticación, elegí tu cuenta en el asistente de inicio de sesión.
5. Si no abre navegador por SSH, abrí en tu computadora el enlace que muestra la terminal. Si el navegador devuelve un código, pegalo en el prompt de esa terminal. Al terminar debería aparecer `Login successful`.

[Seguro] La instalación y disponibilidad del comando están probadas; la sesión interactiva autenticada queda pendiente de tu ingreso. Fuente: [autenticación oficial de Claude Code](https://code.claude.com/docs/en/authentication).
