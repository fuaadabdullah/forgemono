.PHONY: help encrypt decrypt rotate validate apply clean

# Environment (dev, staging, prod)
ENV ?= dev

# Kubernetes namespace
NAMESPACE ?= overmind-$(ENV)

# SOPS binary
SOPS := $(shell command -v sops 2> /dev/null)

# age binary
AGE := $(shell command -v age 2> /dev/null)

help: ## Show this help
	@echo "SOPS Secrets Management"
	@echo ""
	@echo "Usage: make <target> ENV=<env> [NAMESPACE=<ns>]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

check-deps: ## Check required dependencies
	@command -v sops >/dev/null 2>&1 || { echo "Error: sops not installed. Run: brew install sops"; exit 1; }
	@command -v age >/dev/null 2>&1 || { echo "Error: age not installed. Run: brew install age"; exit 1; }
	@test -f ~/.config/sops/age/keys.txt || { echo "Error: age key not found. Run: age-keygen -o ~/.config/sops/age/keys.txt"; exit 1; }
	@echo "✓ All dependencies installed"

encrypt: check-deps ## Encrypt all files in ENV directory
	@echo "Encrypting secrets for $(ENV) environment..."
	@for file in $(ENV)/*.yaml; do \
		if [ -f "$$file" ] && [[ "$$file" != *.enc.yaml ]]; then \
			echo "  - Encrypting $$file"; \
			sops -e "$$file" > "$${file%.yaml}.enc.yaml"; \
		fi \
	done
	@echo "✓ Encryption complete"

decrypt: check-deps ## Decrypt all files in ENV directory (for local testing)
	@echo "Decrypting secrets for $(ENV) environment..."
	@for file in $(ENV)/*.enc.yaml; do \
		if [ -f "$$file" ]; then \
			echo "  - Decrypting $$file"; \
			sops -d "$$file" > "$${file%.enc.yaml}.dec.yaml"; \
		fi \
	done
	@echo "✓ Decryption complete"
	@echo "⚠️  Warning: .dec.yaml files are gitignored - do not commit!"

rotate: check-deps ## Rotate encryption keys for all files
	@echo "Rotating keys for $(ENV) environment..."
	@for file in $(ENV)/*.enc.yaml; do \
		if [ -f "$$file" ]; then \
			echo "  - Rotating $$file"; \
			sops updatekeys "$$file"; \
		fi \
	done
	@echo "✓ Key rotation complete"

validate: check-deps ## Validate all encrypted files can be decrypted
	@echo "Validating secrets for $(ENV) environment..."
	@for file in $(ENV)/*.enc.yaml; do \
		if [ -f "$$file" ]; then \
			echo -n "  - Validating $$file... "; \
			sops -d "$$file" > /dev/null 2>&1 && echo "✓" || echo "✗ FAILED"; \
		fi \
	done
	@echo "✓ Validation complete"

apply: check-deps ## Decrypt and apply secrets to Kubernetes
	@echo "Applying secrets to $(NAMESPACE) namespace..."
	@for file in $(ENV)/*.enc.yaml; do \
		if [ -f "$$file" ]; then \
			echo "  - Applying $$file"; \
			sops -d "$$file" | kubectl apply -n $(NAMESPACE) -f -; \
		fi \
	done
	@echo "✓ Secrets applied"

clean: ## Remove decrypted .dec.yaml files
	@echo "Cleaning decrypted files..."
	@find . -name "*.dec.yaml" -delete
	@echo "✓ Cleanup complete"

show-public-key: check-deps ## Show your age public key
	@echo "Your age public key (share with team):"
	@age-keygen -y ~/.config/sops/age/keys.txt

edit: check-deps ## Edit encrypted secret: make edit FILE=dev/litellm-secrets.enc.yaml
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE not specified. Usage: make edit FILE=dev/litellm-secrets.enc.yaml"; \
		exit 1; \
	fi
	@sops $(FILE)

view: check-deps ## View encrypted secret: make view FILE=dev/litellm-secrets.enc.yaml
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE not specified. Usage: make view FILE=dev/litellm-secrets.enc.yaml"; \
		exit 1; \
	fi
	@sops -d $(FILE)
