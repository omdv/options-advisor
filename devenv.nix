{ pkgs, ... }:
{
  packages = with pkgs; [
    pulumi-bin
    pre-commit
    go-task
  ];

  languages.python = {
    enable = true;
    package = pkgs.python313;

    venv.enable = true;

    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };
}
