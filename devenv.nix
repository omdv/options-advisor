{ pkgs, ... }: {
  packages = [
    pkgs.pulumi-bin
    pkgs.go-task
  ];

  languages.python = {
    enable = true;
    poetry = {
      enable = true;
      install = {
        enable = true;
        groups = [ "main" "dev" ];
        allExtras = true;
      };
    };
    version = "3.10.10";
  };
}
