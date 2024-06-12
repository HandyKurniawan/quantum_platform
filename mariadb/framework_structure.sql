CREATE DATABASE  IF NOT EXISTS `framework` /*!40100 DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci */;
USE `framework`;
-- MySQL dump 10.13  Distrib 8.0.34, for Linux (x86_64)
--
-- Host: ec2-13-60-50-75.eu-north-1.compute.amazonaws.com    Database: framework
-- ------------------------------------------------------
-- Server version	5.5.5-10.5.20-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `calibration`
--

DROP TABLE IF EXISTS `calibration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calibration` (
  `type` varchar(10) NOT NULL,
  `display_name` varchar(45) DEFAULT NULL,
  `description` varchar(100) DEFAULT NULL,
  `days` int(11) DEFAULT NULL,
  `adjust` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `circuit`
--

DROP TABLE IF EXISTS `circuit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `circuit` (
  `name` varchar(45) NOT NULL,
  `qasm` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `depth` int(11) DEFAULT NULL,
  `total_gates` int(11) DEFAULT NULL,
  `gates` longtext DEFAULT NULL,
  `correct_output` longtext DEFAULT NULL,
  `qubit` int(11) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `compilation_technique`
--

DROP TABLE IF EXISTS `compilation_technique`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compilation_technique` (
  `compilation_name` varchar(45) NOT NULL,
  `display_name` varchar(70) DEFAULT NULL,
  `mapping` varchar(45) DEFAULT NULL,
  `mapping_noise_aware` tinyint(1) DEFAULT NULL,
  `routing` varchar(45) DEFAULT NULL,
  `routing_noise_aware` tinyint(1) DEFAULT NULL,
  `calibration_type` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`compilation_name`),
  KEY `fk_compilation_technique_1_idx` (`calibration_type`),
  CONSTRAINT `fk_compilation_technique_1` FOREIGN KEY (`calibration_type`) REFERENCES `calibration` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hardware`
--

DROP TABLE IF EXISTS `hardware`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hardware` (
  `hw_name` varchar(25) NOT NULL,
  `hw_provider` varchar(45) NOT NULL,
  `number_of_qubit` int(11) NOT NULL,
  `hw_description` varchar(100) NOT NULL,
  `2q_native_gates` varchar(45) DEFAULT NULL,
  `status` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`hw_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `metric`
--

DROP TABLE IF EXISTS `metric`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `metric` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `detail_id` int(11) NOT NULL,
  `total_gate` int(11) DEFAULT NULL,
  `total_one_qubit_gate` int(11) DEFAULT NULL,
  `total_two_qubit_gate` int(11) DEFAULT NULL,
  `circuit_depth` int(11) DEFAULT NULL,
  `circuit_cost` float DEFAULT NULL,
  `success_rate_tvd` float DEFAULT NULL,
  `success_rate_nassc` float DEFAULT NULL,
  `success_rate_quasi` float DEFAULT NULL,
  `success_rate_polar` float DEFAULT NULL,
  `hellinger_distance` float DEFAULT NULL,
  `success_rate_tvd_new` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_metric_1_idx` (`detail_id`),
  CONSTRAINT `fk_metric_1` FOREIGN KEY (`detail_id`) REFERENCES `result_detail` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19490 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `qiskit_token`
--

DROP TABLE IF EXISTS `qiskit_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qiskit_token` (
  `token` varchar(200) NOT NULL,
  `str_instance` varchar(100) DEFAULT NULL,
  `int_quota` int(11) DEFAULT NULL,
  `int_usage` int(11) DEFAULT NULL,
  `int_remaining` int(11) DEFAULT NULL,
  `int_pending_jobs` int(11) DEFAULT NULL,
  `int_max_pending_jobs` int(11) DEFAULT NULL,
  `str_email` varchar(200) DEFAULT NULL,
  `str_plan` varchar(45) DEFAULT NULL,
  `description` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`token`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `result`
--

DROP TABLE IF EXISTS `result`;
/*!50001 DROP VIEW IF EXISTS `result`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `result` AS SELECT 
 1 AS `header_id`,
 1 AS `user_id`,
 1 AS `hw_name`,
 1 AS `qiskit_token`,
 1 AS `job_id`,
 1 AS `status`,
 1 AS `circuit_name`,
 1 AS `detail_id`,
 1 AS `compilation_name`,
 1 AS `noisy_simulator`,
 1 AS `noise_level`,
 1 AS `updated_qasm`,
 1 AS `original_qasm`,
 1 AS `qubit`,
 1 AS `circuit_depth`,
 1 AS `total_two_qubit_gate`,
 1 AS `success_rate_nassc`,
 1 AS `success_rate_tvd`,
 1 AS `success_rate_tvd_new`,
 1 AS `success_rate_quasi`,
 1 AS `success_rate_polar`,
 1 AS `correct_output`,
 1 AS `quasi_dists`,
 1 AS `shots`,
 1 AS `mapping_json`,
 1 AS `initial_mapping`,
 1 AS `final_mapping`,
 1 AS `str_email`,
 1 AS `int_remaining`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `result_backend_json`
--

DROP TABLE IF EXISTS `result_backend_json`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `result_backend_json` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `detail_id` int(11) NOT NULL,
  `quasi_dists` longtext DEFAULT NULL,
  `quasi_dists_std` longtext DEFAULT NULL,
  `qasm` longtext DEFAULT NULL,
  `shots` int(11) DEFAULT NULL,
  `mapping_json` longtext DEFAULT NULL,
  `mitigation_overhead` decimal(8,4) DEFAULT NULL,
  `mitigation_time` decimal(7,4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_result_backend_json_1_idx` (`detail_id`),
  CONSTRAINT `fk_result_backend_json_1` FOREIGN KEY (`detail_id`) REFERENCES `result_detail` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22150 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `result_detail`
--

DROP TABLE IF EXISTS `result_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `result_detail` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `header_id` int(11) DEFAULT NULL,
  `circuit_name` varchar(45) DEFAULT NULL,
  `compilation_name` varchar(45) DEFAULT NULL,
  `compilation_time` float DEFAULT NULL,
  `initial_mapping` varchar(1500) DEFAULT NULL,
  `final_mapping` longtext DEFAULT NULL,
  `noisy_simulator` tinyint(1) unsigned DEFAULT NULL,
  `noise_level` float DEFAULT NULL,
  `created_datetime` datetime DEFAULT NULL,
  `updated_datetime` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_result_detail_1_idx` (`header_id`),
  KEY `fk_result_detail_2_idx` (`circuit_name`),
  KEY `fk_result_detail_3_idx` (`compilation_name`),
  CONSTRAINT `fk_result_detail_1` FOREIGN KEY (`header_id`) REFERENCES `result_header` (`id`),
  CONSTRAINT `fk_result_detail_2` FOREIGN KEY (`circuit_name`) REFERENCES `circuit` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=26981 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `result_header`
--

DROP TABLE IF EXISTS `result_header`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `result_header` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `hw_name` varchar(50) DEFAULT NULL,
  `qiskit_token` varchar(150) DEFAULT NULL,
  `job_id` varchar(150) DEFAULT NULL,
  `shots` int(11) DEFAULT NULL,
  `runs` int(11) DEFAULT NULL,
  `status` varchar(45) DEFAULT NULL,
  `execution_time` float DEFAULT NULL,
  `job_created_datetime` datetime DEFAULT NULL,
  `job_in_queue_second` decimal(15,5) DEFAULT NULL,
  `job_running_datetime` datetime DEFAULT NULL,
  `job_completed_datetime` datetime DEFAULT NULL,
  `created_datetime` datetime DEFAULT NULL,
  `updated_datetime` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_result_header_1_idx` (`user_id`),
  KEY `fk_result_header_2_idx` (`hw_name`),
  CONSTRAINT `fk_result_header_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_result_header_2` FOREIGN KEY (`hw_name`) REFERENCES `hardware` (`hw_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2929 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `result_updated_qasm`
--

DROP TABLE IF EXISTS `result_updated_qasm`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `result_updated_qasm` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `detail_id` int(11) DEFAULT NULL,
  `updated_qasm` longtext DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_result_updated_qasm_1_idx` (`detail_id`),
  CONSTRAINT `fk_result_updated_qasm_1` FOREIGN KEY (`detail_id`) REFERENCES `result_detail` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26627 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(45) DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `password` varchar(45) DEFAULT NULL,
  `active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`user_id`),
  KEY `idx_user_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=100 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'framework'
--

--
-- Dumping routines for database 'framework'
--

--
-- Final view structure for view `result`
--

/*!50001 DROP VIEW IF EXISTS `result`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`handy`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `result` AS select `h`.`id` AS `header_id`,`h`.`user_id` AS `user_id`,`h`.`hw_name` AS `hw_name`,`h`.`qiskit_token` AS `qiskit_token`,`h`.`job_id` AS `job_id`,`h`.`status` AS `status`,`d`.`circuit_name` AS `circuit_name`,`d`.`id` AS `detail_id`,`d`.`compilation_name` AS `compilation_name`,`d`.`noisy_simulator` AS `noisy_simulator`,`d`.`noise_level` AS `noise_level`,`q`.`updated_qasm` AS `updated_qasm`,`c`.`qasm` AS `original_qasm`,`c`.`qubit` AS `qubit`,`m`.`circuit_depth` AS `circuit_depth`,`m`.`total_two_qubit_gate` AS `total_two_qubit_gate`,`m`.`success_rate_nassc` AS `success_rate_nassc`,`m`.`success_rate_tvd` AS `success_rate_tvd`,`m`.`success_rate_tvd_new` AS `success_rate_tvd_new`,`m`.`success_rate_quasi` AS `success_rate_quasi`,`m`.`success_rate_polar` AS `success_rate_polar`,`c`.`correct_output` AS `correct_output`,`j`.`quasi_dists` AS `quasi_dists`,`j`.`shots` AS `shots`,`j`.`mapping_json` AS `mapping_json`,`d`.`initial_mapping` AS `initial_mapping`,`d`.`final_mapping` AS `final_mapping`,`t`.`str_email` AS `str_email`,`t`.`int_remaining` AS `int_remaining` from ((((((`result_header` `h` join `result_detail` `d` on(`h`.`id` = `d`.`header_id`)) left join `result_backend_json` `j` on(`j`.`detail_id` = `d`.`id`)) left join `result_updated_qasm` `q` on(`q`.`detail_id` = `d`.`id`)) join `circuit` `c` on(`d`.`circuit_name` = `c`.`name`)) left join `metric` `m` on(`d`.`id` = `m`.`detail_id`)) left join `qiskit_token` `t` on(`h`.`qiskit_token` = `t`.`token`)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-06-11 11:19:49
