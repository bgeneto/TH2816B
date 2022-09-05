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
      debug: true,
      fallbackLng: 'en',
      resources: {
        en: {
          translation: {
            head: {
              title: 'TH2816B LCR Meter WebGUI',
              description: 'Web interface for TH2816B LCR Meter data processing'
            },
            intro: {
              title: 'TH2816B LCR Meter WebGUI',
              subtitle: 'Web interface for TH2816B LCR Meter data processing'
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
              index: 'TH2816B I/O',
              page1: 'Experiment',
              page2: 'Arduino'
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
              description: 'Interface web para aquisição de dados do LCR Meter TH2816B'
            },
            intro: {
              title: 'TH2816B LCR Meter WebGUI',
              subtitle: 'Interface web para aquisição de dados do LCR Meter TH2816B'
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
              index: 'TH2816B E/S',
              page1: 'Experimento',
              page2: 'Arduino'
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