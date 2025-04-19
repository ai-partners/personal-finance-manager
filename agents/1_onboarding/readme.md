# ai-personal-accountant

# Recursos en Azure
- Inicialmente cree un grupo de recursos llamado ai-personal-accountant para disponer todos los servicios que se crearían. En este grupo de recursos se creo la instancia de base de datos y una instancia de ai foundry básica. Cuando intenté crear unos ejemplos de agentes con funciones tuve problemas por el tipo de instalación "básica", luego ampliaré en detalles. En este sentido, tuve que crear un nuevo grupo de recursos (ai-partners), para la implementación "estandar" de ai foundry, dado que el nombre del anterior (ai-personal-accountant), era muy extenso para la implementación a través de la plantilla bicep. En ultimas, el grupo de recursos que estoy utilizando para todo lo del agente es el de ai-partners; sería bueno pasar la base de datos al nuevo grupo de recursos y dar de baja el anterior, con el fin de mantener todo centralizado.
- Hay otro grupo de recursos llamado az-functions-rg que tiene unas funciones que estuve probando, lo dejaré temporalmente por si llegamos a necesitar azure functions.

# Changelog
Daniel (18/04):
- Se cambio el enfoque de invocación de las funciones de logic apps. Ahora se hace por OpenApi, dado que con el enfoque de custom functions, estas solo son ejecutables en el runtime del creador del agente (dónde se define su implementación), pero para otro agente u orquestador esta implementación sería desconocida.
- Con el cambio anterior, ahora este agente puede ser testeado en el playground de AI Foundry y también invocado (con todas sus funciones) desde un orquestador, como por ejemplo el Semantic Kernel, sin necesidad de re-implementar las funciones en el kernel (plugins).

Daniel (18/04):
- Se agregó la carpeta de agents, para organizar los agentes
- Se agregó el agente 1, el cual tiene como responsabilidad realizar el onboarding a la app, registrando las cuentas y categorías que se utilizarán en el registro de transacciones
- Se agregaron las funciones de record_account y record_category para realizar la creación de registros en la base de datos (usando logic apps)

# To do
- Pasar instancia de bd al grupo de recursos principal (ai-partners)
- Pensar como se va hacer el registro de usuario, para poder usar el user_id del usuario logueado en la app en la creación de registros. Por el momento estoy enviando el parametro en el prompt pero no debe quedar así.
- Respecto al punto anterior hay que cambiar el tipo de dato del user_id, ahorita es entero, pero seguramente no es el tipo de dato correcto.
- En la creación de cuentas veo que es necesario establecer un saldo inicial, es decir llamar al agente 2 para que cree un registro inicial con ese saldo. Por ejemplo, si es una cuenta bancaria se debería indicar el saldo actual. Si es un crédito, se debería indicar el valor de la deuda (valor negativo).
- Sería bueno incluir la posibilidad de editar cuentas y categorías que ya existan, pero creo que puede ser al final, por ahora podemos concentrarnos en features que sean core del caso de uso
