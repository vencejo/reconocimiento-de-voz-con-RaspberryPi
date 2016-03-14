Reconocimiento de voz con Raspberry Pi
======================================

Programa para experimentar con el reconocimiento de voz en castellano en la Raspberry Pi usando servicios en la nube.

Se basa en la arquitectura del proyecto [jasperproject.github.io](http://jasperproject.github.io/) .

Entre otros cambios, se ha intentado hacerlo mas pythonico añadiéndole la libreria [speech_recognition](https://github.com/Uberi/speech_recognition) .

También se ha limitado el número de motores de reconocimiento a dos: el de IBM y el de AT&T

## Uso

Lo primero que hay que hacer es ejecutar client/populate.py para guardar la configuracion de trabajo

Después se ejecuta el programa principal jasper.py


## License

Jasper is covered by the MIT license, a permissive free software license that lets you do anything you want with the source code, as long as you provide back attribution and ["don't hold \[us\] liable"](http://choosealicense.com). For the full license text see the [LICENSE.md](LICENSE.md) file.

*Note that this licensing only refers to the Jasper client code (i.e.,  the code on GitHub) and not to the disk image itself (i.e., the code on SourceForge).*
