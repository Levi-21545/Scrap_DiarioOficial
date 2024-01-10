create table servidores
(
    id           int auto_increment
        primary key,
    nome         varchar(60)  not null,
    materia      int          not null,
    data         date         not null,
    id_func      varchar(10)  not null,
    tipo_vinculo varchar(30)  null,
    cargo_funcao varchar(255) null
);