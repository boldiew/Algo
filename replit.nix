{ pkgs }: {
  deps = [
    pkgs.bashInteractive
    pkgs.python311
    pkgs.python311Packages.pip
  ];
}
