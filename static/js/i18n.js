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
              error: 'Error starting the experiment. Please check parameters'
            },
            menu: {
              pages: 'Pages',
              index: 'TH2816B I/O',
              page1: 'Connection',
              page2: 'Experiment'
            },
            page1: {
              title: 'Connect devices',
              button: 'Connect'
            },
            page2: {
              title: 'Experiment Config',
              num_sensors: 'Number of Sensors',
              duration: 'Duration of each sensor reading',
              duration_help: 'seconds',
              sensor1: 'Sensor 1',
              sensor1: 'Sensor 2',
              button: 'Start experiment'
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
              error: 'Erro ao iniciar o experimento. Cheque os parâmetros configurados.'
            },
            menu: {
              pages: 'Páginas',
              index: 'TH2816B E/S',
              page1: 'Conexão',
              page2: 'Experimento'
            },
            page1: {
              title: 'Conectar dispositivos',
              button: 'Conectar'
            },
            page2: {
              title: 'Configuração do Experimento',
              num_sensors: 'Número de sensores',
              duration: 'Duração de leitura cada sensor',
              duration_help: 'segundos',
              sensor1: 'Sensor 1',
              sensor1: 'Sensor 2',
              button: 'Iniciar experimento'
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
        const chosenLng = $(this).find("option:selected").attr('value');
        i18next.changeLanguage(chosenLng, () => {
          rerender();
        });
      });

      rerender();
    });
});