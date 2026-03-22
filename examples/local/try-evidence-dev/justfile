default:
  @just --list

# Setup new project from template
ev-setup-proj project_name:
    npx degit evidence-dev/template {{project_name}} && \
    cd {{project_name}} && \
    npm install && \
    npm run sources && \
    npm run dev 