; Instalador do AgentQuest HQ (Inno Setup 6)
; Gerado a partir da saída onedir do PyInstaller em build\dist\AgentQuestHQ.
; Compile via: python scripts\build_release.py

#define AppName "AgentQuest HQ"
#define AppVersion "1.0.0"
#define AppPublisher "AgentQuest"
#define AppExeName "AgentQuestHQ.exe"

[Setup]
AppId={{8E4C1A72-9D3F-4B58-A6E1-2F7C5B9D0E31}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\AgentQuest HQ
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Instala no perfil do usuário — não exige privilégio de administrador.
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=AgentQuestHQ-Setup-{#AppVersion}
SetupIconFile=assets\agentquest.ico
; Ícone exibido em "Aplicativos instalados" do Windows
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"
Name: "startupicon"; Description: "Iniciar o AgentQuest HQ automaticamente ao ligar o computador"; GroupDescription: "Inicialização:"; Flags: unchecked

[Files]
Source: "dist\AgentQuestHQ\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "AgentQuestHQ"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar o {#AppName} agora"; Flags: nowait postinstall skipifsilent

[Code]
// Ao desinstalar, pergunta se os dados do usuário (cofre Obsidian, configurações,
// banco e arquivos processados) devem ser apagados. O padrão é preservar, para
// não destruir dados reais de clientes por acidente.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataPaths: array[0..5] of String;
  I: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Em modo silencioso não há como perguntar — nesse caso os dados são SEMPRE
    // preservados, para que uma desinstalação automatizada nunca apague o cofre
    // e as configurações do usuário sem confirmação explícita.
    if UninstallSilent then
      Exit;

    if MsgBox('Deseja apagar TAMBÉM seus dados do AgentQuest HQ?' + #13#10 + #13#10 +
              'Isso inclui o cofre Obsidian (vault), suas configurações, o banco de dados ' +
              'e os arquivos processados.' + #13#10 + #13#10 +
              'Escolha "Não" para manter seus dados caso pretenda reinstalar depois.',
              mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
    begin
      DataPaths[0] := ExpandConstant('{app}\vault');
      DataPaths[1] := ExpandConstant('{app}\inbox');
      DataPaths[2] := ExpandConstant('{app}\processed');
      DataPaths[3] := ExpandConstant('{app}\outputs');
      DataPaths[4] := ExpandConstant('{app}\settings.json');
      DataPaths[5] := ExpandConstant('{app}\backend\database.sqlite3');

      for I := 0 to 5 do
      begin
        if DirExists(DataPaths[I]) then
          DelTree(DataPaths[I], True, True, True)
        else if FileExists(DataPaths[I]) then
          DeleteFile(DataPaths[I]);
      end;

      DelTree(ExpandConstant('{app}'), True, True, True);
    end;
  end;
end;
