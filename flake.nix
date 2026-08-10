{
  description = "fnv-mod-manager";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = [ pkgs.python312 pkgs.python312Packages.pytest pkgs.ruff pkgs.uv pkgs.p7zip pkgs.python312Packages.tomlkit ];
        shellHook = ''
          if [ ! -d .venv ]; then
            uv venv .venv
          fi
          source .venv/bin/activate
          uv pip install -e . --quiet
        '';
      };
    };
}
