const lngs = {
  en: { nativeName: 'English' },
  pt: { nativeName: 'Português' }
};

const rerender = () => {
  // start localizing, details:
  // https://github.com/i18next/jquery-i18next#usage-of-selector-function
  $('body').localize();
  $('title').text($.t('head.title'))
  $('meta[name=description]').attr('content', $.t('head.description'))
}

$(function () {
  // use plugins and options as needed, for options, detail see
  // https://www.i18next.com
  i18next
    // detect user language
    // learn more: https://github.com/i18next/i18next-browser-languageDetector
    .use(i18nextBrowserLanguageDetector)
    // init i18next
    // for all options read: https://www.i18next.com/overview/configuration-options
    .init({
      debug: false,
      fallbackLng: 'pt',
      resources: {
        en: {
          translation: {
            head: {
              title: 'TH2816B LCR Meter WebGUI',
              description: 'Web interface for experiments with data acquisition via TH2816B LCR Meter'
            },
            intro: {
              title: 'TH2816B LCR Meter WebGUI',
              subtitle: 'Web interface for experiments with data acquisition via TH2816B LCR Meter'
            },
            promo: {
              title: 'Warning',
              text: 'No warnings today'
            },
            data: {
              output: 'TH2816B data output',
              input: 'TH2816B data input',
              output_label: 'Serial port output',
              button: 'Clear'
            },
            command: {
              label: 'Send Command',
              placeholder: 'Type your command here...',
              button: 'Send',
              err: 'The following commands failed, please try again:',
              ok: 'All commands sent successfully!',
              sent: 'Experiment started successfully!',
              error: 'Error configuring the experiment. Please check parameters.'
            },
            menu: {
              pages: 'Pages',
              config: 'Configuration',
              index: 'New Experiment',
              page1: 'Experiment',
              page2: 'Arduino',
              page3: 'Communication',
              page4: 'Results',
              experiment: 'Experiment',
            },
            index: {
              title: 'New Experiment',
              exp_name: 'Description of the Experiment',
              exp_desc: 'Describe your experiment',
              button: 'Start Experiment',
              clr_button: 'Clear',
              output: 'Data output',
              ok_msg: 'Experiment started successfully!',
              log: 'Waiting for an experiment...',
              username: 'Username',
            },
            page1: {
              title: 'Experiment Configuration',
              button: 'Config experiment',
              sensor_duration: 'Duration of each sensor reading:',
              duration_help: 'seconds',
              loop_help: 'repeat',
              sensors_loop: 'Number of repetitions for sensors:',
              valves_loop: 'Number of repetitions for valves:',
              ok_msg: 'Experiment configured successfully!',
              ok_msg_title: 'Sucess',
              err_msg: 'Could not configure experiment parameters!',
            },
            page2: {
              title: 'Arduino Config',
              text: "Don't forget to configure the <a href='/page?id=1'>experiment</a> (and the <a href='/page?id=2'>arduino</a>) before starting!",
              text: 'Inform below which Arduino pins are configured for each sensor (or valve).<br> Leave blank to not configure an arduino, sensor, or valve.<br>',
              num_sensors: 'Number of Sensors',
              sensor1: 'Sensor 1',
              sensor2: 'Sensor 2',
              button: 'Config arduino',
              A1pins: '➲ ARDUINO 1 - PINS',
              A2pins: '➲ ARDUINO 2 - PINS',
              sensors: 'Sensors <span><i class="lni lni-question-circle" title="input example: D8 or D22,D23 (two pins for one sensor)"></i></span>',
              valves: 'Valves <span><i class="lni lni-question-circle" title="input example: D8 or D22,D23 (two pins for one valve)"></i></span>',
              S01: 'S01',
              S02: 'S02',
              S03: 'S03',
              S04: 'S04',
              S05: 'S05',
              S06: 'S06',
              S07: 'S07',
              S08: 'S08',
              V01: 'V01',
              V02: 'V02',
              V03: 'V03',
              V04: 'V04',
              V05: 'V05',
              V06: 'V06',
              V07: 'V07',
              V08: 'V08',
              ok_msg: 'Arduinos configured successfully!',
              ok_msg_title: 'Sucess',
              err_msg: 'Could not configure arduinos!',
              arduino_model: 'Arduino Model',
              onoff: 'Invert ON/OFF relay logic',
            },
            page3: {
              title: 'Use this page to send commands to and receive data from the TH2816B LCR Meter',
            },
            page4: {
              title: 'Finished Experiments',
            },
            configure: {
              button: 'Configure'
            }
          }
        },
        pt: {
          translation: {
            head: {
              title: 'TH2816B LCR Meter WebGUI',
              description: 'Interface web para experimentação com aquisição de dados via LCR Meter TH2816B'
            },
            intro: {
              title: 'TH2816B LCR Meter WebGUI',
              subtitle: 'Interface web para experimentação com aquisição de dados via LCR Meter TH2816B'
            },
            promo: {
              title: 'Aviso',
              text: 'Estamos 0 dias sem acidentes'
            },
            data: {
              output: 'Saída de dados',
              input: 'Entrada de dados',
              output_label: 'Saída da porta serial',
              button: 'Limpar'
            },
            command: {
              label: 'Enviar Comando',
              placeholder: 'Digite seu comando aqui...',
              button: 'Enviar',
              err: 'Os seguintes comandos falharam, tente novamente:',
              ok: 'Todos os comandos foram registrados com sucesso!',
              sent: 'Experimento iniciado com sucesso!',
              error: 'Erro ao configurar o experimento. Cheque os parâmetros.'
            },
            menu: {
              pages: 'Páginas',
              config: 'Configuração',
              index: 'Novo Experimento',
              page1: 'Experimento',
              page2: 'Arduino',
              page3: 'Comunicação',
              page4: 'Resultados',
              experiment: 'Experimento',
            },
            index: {
              title: 'Novo Experimento',
              text: 'Não esqueça de configurar o <a href="/page?id=1">experimento</a> (e o <a href="/page?id=2">arduino</a>) antes de iniciar!',
              exp_name: 'Descrição do Experimento',
              exp_desc: 'Descreva seu experimento',
              button: 'Iniciar Experimento',
              clr_button: 'Limpar',
              output: 'Saída de dados',
              ok_msg: 'Experimento iniciado com sucesso!',
              log: 'Aguardando novo experimento...',
              username: 'Nome do usuário',
            },
            page1: {
              title: 'Configuração do Experimento',
              button: 'Configurar experimento',
              sensors_duration: 'Duração de leitura cada sensor:',
              duration_help: 'segundos',
              loop_help: 'repetições',
              sensors_loop: 'Quantidade de repetições para os sensores:',
              valves_loop: 'Quantidade de repetições para as válvulas:',
              ok_msg: 'Experimento configurado com sucesso!',
              ok_msg_title: 'Sucesso',
              err_msg: 'Não foi possível configurar o experimento!',
            },
            page2: {
              title: 'Configuração do Arduino',
              text: 'Informe abaixo quais pinos do arduino estão ligados em cada sensor (ou válvula).<br> Deixe em branco para não configurar um arduino, sensor ou válvula.<br>',
              num_sensors: 'Número de sensores',
              sensor1: 'Sensor 1',
              sensor2: 'Sensor 2',
              button: 'Configurar arduino',
              A1pins: 'ARDUINO 1 - PINOS',
              A2pins: 'ARDUINO 2 - PINOS',
              sensors: 'Sensores <span><i class="lni lni-question-circle" title="exemplo: D8 ou D22,D23 (dois pinos para um sensor)"></i></span>',
              valves: 'Válvulas <span><i class="lni lni-question-circle" title="exemplo: D8 ou D22,D23 (dois pinos para uma válvula)"></i></span>',
              S01: 'S01',
              S02: 'S02',
              S03: 'S03',
              S04: 'S04',
              S05: 'S05',
              S06: 'S06',
              S07: 'S07',
              S08: 'S08',
              V01: 'V01',
              V02: 'V02',
              V03: 'V03',
              V04: 'V04',
              V05: 'V05',
              V06: 'V06',
              V07: 'V07',
              V08: 'V08',
              ok_msg: 'Arduinos configurados com sucesso!',
              ok_msg_title: 'Sucesso',
              err_msg: 'Não foi possível configurar o arduino!',
              arduino_model: 'Modelo do Arduino',
              onoff: 'Inverter lógica ON/OFF do relay',
            },
            page3: {
              title: 'Use esta página para enviar comandos e visualizar os dados capturados pelo medidor LCR TH2816B',
            },
            page4: {
              title: 'Experimentos Concluídos',
            },
            configure: {
              button: 'Configure'
            }
          }
        }
      }
    }, (err, t) => {
      if (err) return console.error(err);

      // for options see
      // https://github.com/i18next/jquery-i18next#initialize-the-plugin
      jqueryI18next.init(i18next, $, { useOptionsAttr: true });

      // fill language switcher
      Object.keys(lngs).map((lng) => {
        const opt = new Option(lngs[lng].nativeName, lng);
        if (lng === i18next.resolvedLanguage) {
          opt.setAttribute("selected", "selected");
        }
        $('#languageSwitcher').append(opt);
      });
      $('#languageSwitcher').change((a, b, c) => {
        const chosenLng = $('#languageSwitcher').find("option:selected").attr('value');
        i18next.changeLanguage(chosenLng, () => {
          rerender();
        });
      });

      rerender();
    });
});