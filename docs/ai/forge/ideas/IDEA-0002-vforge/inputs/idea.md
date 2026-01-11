The idea is to develop a web application, VibeForge, **An AI-powered application factory** that generates working apps from structured questionnaires (no free-text input).

The app has 2 "modes"; session and control panel. Session is directed towards the end user, while /control is targeted for the admin user.

Desired session workflow: User fills a questionnaire -> a plan / idea for the app is generated -> User verifies the plan -> Plan is forwarded to a specific agent, the orchestrator, that then divides the plan into subtasks and forwards them to other agents of various roles. The roles are:

- Foreman (defines the necessary code snippets, forwards tasks to workers)
- Reviewer (reviews workers' work to ensure quality and requirements are met)
- Worker (writes the actual code)
- Fixer (completes special tasks, such as provides fixes to code that once already once deemed 'working')

During session workflow, there should be clear output to inform the user what is going on (how many agents working, api requests sent etc. metrics).
When the work is done, user is presented with the application code and custom instructions on how to run it.

The control mode allows for full view and customization of the agent pipeline.
In control mode the agents can be used for anything really, not just to create a specific application. In control panel the admin user should be able to run simulations with the agents. This means that each agent can be assigned a role and a task.
Agents should be customizable from the control panel (provider / model, report costs / token usage).
Definition of done for control panel:
The user can select any number of agents for their simulation. The user can assign a role and a task to each agent. While simulation is running, the UI should clearly display the status and output of each agent. This is to ensure the 'workflow' of the agents is captured and displayed clearly. This means that upon clicking further, we can dig down into what each agent is saying or doing, and to which agent they are talking to.
