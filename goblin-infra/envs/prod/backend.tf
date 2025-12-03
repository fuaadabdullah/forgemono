terraform {
  cloud {
    organization = "GoblinOS"

    workspaces {
      name = "GoblinOSAssistant-prod"
    }
  }
}
